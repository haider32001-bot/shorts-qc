"""Pure checks for a YouTube Short, plus ffprobe probing.

The pure functions take plain numbers and return (passed, message),
so they are testable without ffmpeg. ``probe_file`` is the only part
that shells out to ffprobe, and it degrades gracefully when ffprobe
is missing.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    skipped: bool = False


def check_duration(seconds: float, max_duration: float = 60.0) -> CheckResult:
    if seconds <= max_duration:
        return CheckResult("duration", True, f"{seconds:.1f}s (<= {max_duration:g}s)")
    return CheckResult("duration", False, f"{seconds:.1f}s (> {max_duration:g}s)")


def check_vertical_9_16(width: int, height: int, tolerance: float = 0.02) -> CheckResult:
    if height == 0:
        return CheckResult("vertical 9:16", False, "height is 0")
    ratio = width / height
    expected = 9 / 16
    if abs(ratio - expected) <= tolerance:
        return CheckResult("vertical 9:16", True, f"{width}x{height}")
    if width > height:
        hint = "is landscape, not 9:16 vertical"
    else:
        hint = f"ratio {ratio:.3f}, expected 0.5625 (9:16)"
    return CheckResult("vertical 9:16", False, f"{width}x{height} {hint}")


def check_resolution(width: int, height: int, min_width: int = 1080, min_height: int = 1920) -> CheckResult:
    if width >= min_width and height >= min_height:
        return CheckResult("resolution", True, f"{width}x{height}")
    return CheckResult(
        "resolution", False, f"{width}x{height} (< {min_width}x{min_height})"
    )


def check_frame_rate(fps: float, min_fps: float = 24.0) -> CheckResult:
    if fps >= min_fps:
        return CheckResult("frame rate", True, f"{fps:.1f} fps")
    return CheckResult("frame rate", False, f"{fps:.1f} fps (< {min_fps:g} fps)")


def check_audio_present(audio_streams: int) -> CheckResult:
    if audio_streams >= 1:
        return CheckResult("audio present", True, f"{audio_streams} stream(s)")
    return CheckResult("audio present", False, "no audio stream found")


def check_loudness(mean_db: float | None, min_db: float = -30.0) -> CheckResult:
    if mean_db is None:
        return CheckResult(
            "loudness", True, "could not be read, skipped", skipped=True
        )
    if mean_db >= min_db:
        return CheckResult("loudness", True, f"{mean_db:.1f} dB mean")
    return CheckResult("loudness", False, f"{mean_db:.1f} dB mean (< {min_db:g} dB)")


def probe_file(path: str) -> dict:
    """Return ffprobe stream info, or {} when ffprobe is unavailable."""
    if shutil.which("ffprobe") is None:
        return {}
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", path,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (subprocess.SubprocessError, OSError):
        return {}
    if out.returncode != 0:
        return {}
    try:
        return json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def _parse_fps(value: str | None) -> float:
    if not value:
        return 0.0
    if "/" in value:
        num, _, den = value.partition("/")
        try:
            return float(num) / float(den) if float(den) else 0.0
        except ValueError:
            return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def check_file(path: str, max_duration: float = 60.0,
               min_width: int = 1080, min_height: int = 1920) -> list[CheckResult]:
    """Run all checks that the available info supports."""
    info = probe_file(path)
    if not info:
        return [CheckResult(
            "probe", False,
            "ffprobe not found or could not read file — install ffmpeg for full checks",
        )]
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_count = sum(1 for s in streams if s.get("codec_type") == "audio")
    fmt = info.get("format", {})
    try:
        duration = float(fmt.get("duration", 0) or 0)
    except (TypeError, ValueError):
        duration = 0.0

    results: list[CheckResult] = [check_duration(duration, max_duration)]
    if video is None:
        results.append(CheckResult("video stream", False, "no video stream found"))
        results.append(check_audio_present(audio_count))
        return results

    width = int(video.get("width", 0) or 0)
    height = int(video.get("height", 0) or 0)
    fps = _parse_fps(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    results.append(check_vertical_9_16(width, height))
    results.append(check_resolution(width, height, min_width, min_height))
    results.append(check_frame_rate(fps))
    results.append(check_audio_present(audio_count))
    # Loudness needs a volumedetect pass; without it we report skipped
    # rather than guessing from stream metadata.
    results.append(check_loudness(None))
    return results


def summarise(results: list[CheckResult]) -> tuple[int, int]:
    passed = sum(1 for r in results if r.passed)
    return passed, len(results)
