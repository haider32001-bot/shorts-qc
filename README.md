# shorts-qc

A small, dependency-free Python CLI that checks a video file before you
upload it as a YouTube Short.

It was built from real upload mistakes: a Short rendered as a 16:9 band
with blurred fill instead of native full-frame 9:16, a file over 60
seconds, low resolution, missing audio, or audio so quiet it is hard to
hear. `shorts-qc` catches those before upload, so the file is fixed
once instead of deleted and re-uploaded.

## Checks

For each file it reports PASS / FAIL for:

- **Duration** — 60 seconds or less (configurable with `--max-duration`)
- **Vertical 9:16** — width / height is 9:16 within tolerance, no
  pillarbox / blurred-fill band
- **Resolution** — at least 1080x1920 by default
  (`--min-width 1080 --min-height 1920`)
- **Frame rate** — 24 fps or higher
- **Audio present** — at least one audio stream
- **Audio loudness** — mean volume above -30 dB, measured with
  ffmpeg `volumedetect` (warns instead of failing when loudness
  cannot be read)
- **Long silence** — no silent gap longer than 2 seconds, measured
  with ffmpeg `silencedetect` (dead air is where viewers swipe away)

It uses `ffprobe` when it is installed. Without `ffprobe` it still
checks what it can from the file itself and clearly says which checks
were skipped, instead of guessing.

## Install

Requires Python 3.9+ and, for full checks, `ffmpeg` (which provides
`ffprobe`).

```bash
pip install .
```

Or run it without installing:

```bash
python -m shorts_qc video.mp4
```

## Usage

```bash
# Basic check — exit code 0 means all checks passed
python -m shorts_qc my-short.mp4

# Allow up to 90 seconds, and print machine-readable JSON
python -m shorts_qc my-short.mp4 --max-duration 90 --json

# Check several files
python -m shorts_qc one.mp4 two.mp4
```

Example output:

```
my-short.mp4
  [PASS] duration: 42.1s (<= 60s)
  [PASS] vertical 9:16: 1080x1920
  [PASS] resolution: 1080x1920
  [PASS] frame rate: 30.0 fps
  [PASS] audio present: 1 stream(s)
  [PASS] loudness: -16.2 dB mean
  [PASS] long silence: longest gap 0.0s (<= 2s)
Result: PASS (7/7)
```

A failing file exits with code 1 and lists exactly what to fix:

```
  [FAIL] vertical 9:16: 1920x1080 is landscape, not 9:16 vertical
  [FAIL] duration: 74.0s (> 60s)
Result: FAIL (5/7)
```

## Why this exists

Shorts are judged in the first second. A wrong aspect ratio, a
too-long file, or inaudible audio wastes the upload slot and the
viewer's first impression. This tool makes the pre-upload check
repeatable: same checks, same report, every file.

## Development

```bash
python -m pytest -q
```

## Contributing

Issues and pull requests are welcome. Please keep checks
deterministic and dependency-free, and add a test for any new check.

## License

MIT — see `LICENSE`.
