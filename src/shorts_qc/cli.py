"""Command-line entry point for shorts-qc."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checker import check_file, summarise


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shorts-qc",
        description="Pre-upload quality checks for YouTube Shorts.",
    )
    p.add_argument("files", nargs="+", help="video file(s) to check")
    p.add_argument("--max-duration", type=float, default=60.0,
                   help="maximum duration in seconds (default: 60)")
    p.add_argument("--min-width", type=int, default=1080)
    p.add_argument("--min-height", type=int, default=1920)
    p.add_argument("--json", action="store_true", help="print JSON report")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    overall_ok = True
    report: dict[str, object] = {}

    for raw in args.files:
        path = Path(raw)
        if not path.is_file():
            print(f"{raw}: file not found", file=sys.stderr)
            overall_ok = False
            report[raw] = {"error": "file not found"}
            continue
        results = check_file(raw, args.max_duration, args.min_width, args.min_height)
        passed, total = summarise(results)
        ok = passed == total
        overall_ok = overall_ok and ok
        report[raw] = {
            "passed": passed, "total": total, "ok": ok,
            "checks": [
                {"name": r.name, "passed": r.passed, "message": r.message,
                 "skipped": r.skipped}
                for r in results
            ],
        }
        if args.json:
            continue
        print(raw)
        for r in results:
            status = "PASS" if r.passed else "FAIL"
            extra = " (skipped)" if r.skipped else ""
            print(f"  [{status}] {r.name}: {r.message}{extra}")
        print(f"Result: {'PASS' if ok else 'FAIL'} ({passed}/{total})")

    if args.json:
        print(json.dumps(report, indent=2))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
