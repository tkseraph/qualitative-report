#!/usr/bin/env python3
"""Capture or verify the stable skeleton of a qualitative Markdown report."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from qualitative_artifacts import compare_structure_snapshot, write_structure_snapshot
except ModuleNotFoundError:  # package import
    from scripts.qualitative_artifacts import compare_structure_snapshot, write_structure_snapshot


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preserve H2 order and chart routing during bounded report revisions"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--capture", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--report", required=True)
    parser.add_argument("--snapshot", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report_path = Path(args.report).expanduser().resolve()
    snapshot_path = Path(args.snapshot).expanduser().resolve()
    if not report_path.is_file():
        print(f"Report not found: {report_path}")
        return 2
    if args.capture:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        write_structure_snapshot(report_path, snapshot_path)
        print(f"Structure snapshot: {snapshot_path}")
        return 0
    if not snapshot_path.is_file():
        print(f"Structure snapshot not found: {snapshot_path}")
        return 2
    errors = compare_structure_snapshot(report_path, snapshot_path)
    for error in errors:
        print(f"[FAIL] {error}")
    print("Qualitative structure validation: " + ("PASS" if not errors else "FAIL"))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
