#!/usr/bin/env python3
"""Create WeChat Official Account drafts from finished Markdown reports."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path

from validate_reports import validate_file

REPORT_TYPES = ("qualitative", "turtle", "valuation")
CREDENTIAL_LIKE_ARGS = {"--appid", "--appsecret", "--secret", "--token"}


def discover_report(path: Path, report_type: str | None, explicit_file: Path | None) -> Path:
    if explicit_file is not None:
        if not explicit_file.exists():
            raise SystemExit(f"Report file not found: {explicit_file}")
        return explicit_file
    if path.is_file():
        if path.suffix.lower() != ".md":
            raise SystemExit(f"Expected a Markdown report file: {path}")
        return path
    if not path.exists():
        raise SystemExit(f"Path not found: {path}")
    if report_type is None:
        raise SystemExit("--type is required when path is an output directory")
    matches = sorted(path.glob(f"*_{report_type}_report.md"))
    if not matches:
        raise SystemExit(f"Missing {report_type} report in: {path}")
    if len(matches) > 1:
        raise SystemExit(
            f"Multiple {report_type} reports found; keep exactly one: "
            + ", ".join(str(match) for match in matches)
        )
    return matches[0]


def infer_report_type(report_path: Path) -> str:
    for report_type in REPORT_TYPES:
        if report_path.name.endswith(f"_{report_type}_report.md"):
            return report_type
    known = ", ".join(f"*_{report_type}_report.md" for report_type in REPORT_TYPES)
    raise SystemExit(f"Cannot infer report type from filename: {report_path.name}. Expected: {known}")


def validate_before_draft(report_path: Path, report_type: str) -> None:
    result = validate_file(report_path, report_type)
    if not result.ok:
        messages = "\n".join(f"- {message}" for message in result.messages)
        raise SystemExit(f"Report validation failed: {report_path}\n{messages}")


def build_wxgzh_command(
    report_path: Path,
    *,
    output_dir: Path,
    account: str | None,
    author: str | None,
    digest: str | None,
    theme: str | None,
    cover: Path | None,
    no_cover: bool,
) -> list[str]:
    command = ["npx", "-y", "@lyhue1991/wxgzh", str(report_path), "--output-dir", str(output_dir)]
    if account:
        command.extend(["--account", account])
    if author:
        command.extend(["--author", author])
    if digest:
        command.extend(["--digest", digest])
    if theme:
        command.extend(["--theme", theme])
    if cover is not None:
        command.extend(["--cover", str(cover)])
    if no_cover:
        command.append("--no-cover")
    return command


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create draft-box entries from finished Turtle Investment Framework reports"
    )
    parser.add_argument("path", type=Path, help="Output directory or Markdown report file")
    parser.add_argument("--type", choices=REPORT_TYPES, help="Report type when path is an output directory")
    parser.add_argument("--file", type=Path, help="Explicit Markdown report file")
    parser.add_argument("--account", help="wxgzh account name")
    parser.add_argument("--author", help="Article author passed to wxgzh")
    parser.add_argument("--digest", help="Article digest passed to wxgzh")
    parser.add_argument("--theme", help="wxgzh theme name")
    parser.add_argument("--cover", type=Path, help="Cover image path passed to wxgzh")
    parser.add_argument("--no-cover", action="store_true", help="Pass --no-cover to wxgzh")
    parser.add_argument("--output-dir", type=Path, help="wxgzh output directory")
    parser.add_argument("--skip-validation", action="store_true", help="Skip finished-report validation")
    parser.add_argument("--dry-run", action="store_true", help="Print the npx command without running it")
    parser.add_argument("--yes", action="store_true", help="Required for real draft creation")
    args, unknown = parser.parse_known_args(argv)
    credential_args = [arg for arg in unknown if arg.split("=", 1)[0].lower() in CREDENTIAL_LIKE_ARGS]
    if credential_args:
        raise SystemExit(
            "Credential-like arguments are not supported: "
            + ", ".join(credential_args)
            + ". Configure wxgzh credentials outside this project."
        )
    if unknown:
        parser.error("unrecognized arguments: " + " ".join(unknown))
    return args


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    report_path = discover_report(args.path, args.type, args.file)
    report_type = args.type or infer_report_type(report_path)
    if not args.skip_validation:
        validate_before_draft(report_path, report_type)
    output_dir = args.output_dir or report_path.parent / ".wxgzh"
    command = build_wxgzh_command(
        report_path,
        output_dir=output_dir,
        account=args.account,
        author=args.author,
        digest=args.digest,
        theme=args.theme,
        cover=args.cover,
        no_cover=args.no_cover,
    )
    if args.dry_run:
        print(shlex.join(command))
        return
    if not args.yes:
        raise SystemExit("--yes is required for real draft creation")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
