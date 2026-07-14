#!/usr/bin/env python3
"""Observable local entry point for qualitative report generation."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

if __package__:
    from .continue_single_stock import _validation_argv, build_step5_prompt, detect_code_prefix
else:
    from continue_single_stock import _validation_argv, build_step5_prompt, detect_code_prefix


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a qualitative report generation prompt from an existing single-stock output directory")
    parser.add_argument("--output-dir", required=True, help="Existing output directory")
    parser.add_argument("--run-nested-claude", action="store_true", help="Call claude -p from this script; off by default because nested Claude is unreliable in Claude Code sessions")
    return parser.parse_args(argv)


def _require_file(path: Path) -> bool:
    if path.exists():
        return True
    print(f"Missing required file: {path}")
    return False


def _model_command(prompt_path: Path) -> list[str]:
    return [
        "claude",
        "-p",
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        "Read,Write",
    ]


def _format_command(command: list[str]) -> str:
    return shlex.join(command)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    required = (
        output_dir / "data_pack_market.md",
        output_dir / "annual_report.pdf",
        output_dir / "pdf_sections.json",
    )
    if not output_dir.exists():
        print(f"Output directory not found: {output_dir}")
        return 2
    for path in required:
        if not _require_file(path):
            return 2

    code_prefix = detect_code_prefix(output_dir)
    target_output = output_dir / f"{code_prefix}_qualitative_report.md"
    prompt_path = output_dir / "step5_qualitative_prompt.md"
    log_path = output_dir / "generate_qualitative.log"
    prompt = build_step5_prompt(project_root, output_dir, target_output)
    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    command = _model_command(prompt_path)
    validation_argv = _validation_argv(project_root, target_output, "qualitative")

    print("[generate] stage=step5 qualitative")
    print(f"[generate] prompt file: {prompt_path}")
    print(f"[generate] target output: {target_output}")
    print(f"[generate] validation command: {_format_command(validation_argv)}")
    if not args.run_nested_claude:
        print("[generate] prompt-only mode: wrote the chain prompt and does not call nested claude -p")
        print("[generate] next action: run the prompt in the current Claude session, then run validation")
        return 0

    print(f"[generate] log file: {log_path}")
    print(f"[generate] model command: {_format_command(command)} < {prompt_path}")
    print("[generate] running nested Claude; output is streamed to log file")
    with prompt_path.open("r", encoding="utf-8") as prompt_file, log_path.open("w", encoding="utf-8") as log_file:
        process = subprocess.run(command, stdin=prompt_file, stdout=log_file, stderr=subprocess.STDOUT, text=True, check=False)
    print(f"[generate] model exit code: {process.returncode}")
    if process.returncode != 0:
        print(f"[generate] failed: inspect log file: {log_path}")
        return process.returncode
    if not target_output.exists():
        print(f"[generate] failed: target output was not created: {target_output}")
        print(f"[generate] inspect log file: {log_path}")
        return 1

    validation = subprocess.run(validation_argv, text=True, check=False)
    print(f"[generate] validation exit code: {validation.returncode}")
    return validation.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
