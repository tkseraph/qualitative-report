#!/usr/bin/env python3
"""Observable local entry point for qualitative report generation."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

try:
    from .qualitative_artifacts import validate_sidecars, write_chain_prompts, write_provenance
    from .qualitative_preflight import audit_inputs, write_manifest
except ImportError:
    from qualitative_artifacts import validate_sidecars, write_chain_prompts, write_provenance
    from qualitative_preflight import audit_inputs, write_manifest

if __package__:
    from .continue_single_stock import (
        _consistency_argv,
        _validation_argv,
        build_step5_prompt,
        detect_code_prefix,
        prepare_computed_metrics,
    )
else:
    from continue_single_stock import (
        _consistency_argv,
        _validation_argv,
        build_step5_prompt,
        detect_code_prefix,
        prepare_computed_metrics,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a qualitative report generation prompt from an existing single-stock output directory")
    parser.add_argument("--output-dir", required=True, help="Existing output directory")
    parser.add_argument("--run-nested-claude", action="store_true", help="Call claude -p from this script; off by default because nested Claude is unreliable in Claude Code sessions")
    parser.add_argument(
        "--profile",
        choices=("draft", "production"),
        default="draft",
        help="production adds audited-input, sidecar and semantic-review barriers",
    )
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
    computed_metrics_path = prepare_computed_metrics(output_dir)
    if args.profile == "production":
        preflight = audit_inputs(output_dir)
        manifest_path = write_manifest(output_dir, preflight)
        print(f"[generate] production input manifest: {manifest_path}")
        for issue in preflight["issues"]:
            level = "ERROR" if issue["blocking"] else "WARN"
            print(f"[generate] {level} {issue['code']}: {issue['message']}")
        if preflight["status"] != "pass":
            print("[generate] production preflight failed")
            return 2
    prompt = build_step5_prompt(project_root, output_dir, target_output)
    prompt_path.write_text(prompt + "\n", encoding="utf-8")
    chain_prompts = write_chain_prompts(project_root, output_dir, target_output)

    command = _model_command(prompt_path)
    consistency_path = output_dir / "consistency_report.md"
    consistency_argv = _consistency_argv(project_root, target_output, consistency_path)
    validation_argv = _validation_argv(project_root, target_output, "qualitative")

    print("[generate] stage=step5 qualitative")
    print(f"[generate] prompt file: {prompt_path}")
    print(f"[generate] target output: {target_output}")
    if args.profile == "production":
        print("[generate] profile=production; evidence and semantic review barriers enabled")
        for stage_path in chain_prompts.values():
            print(f"[generate] chain prompt: {stage_path}")
    if computed_metrics_path:
        print(f"[generate] computed metrics: {computed_metrics_path}")
    else:
        print("[generate] computed metrics unavailable; prompt uses degraded arithmetic rules")
    print(f"[generate] consistency command: {_format_command(consistency_argv)}")
    print(f"[generate] validation command: {_format_command(validation_argv)}")
    if not args.run_nested_claude:
        print("[generate] prompt-only mode: wrote the chain prompt and does not call nested claude -p")
        if args.profile == "production":
            print("[generate] next action: run evidence/argument, draft, independent review and bounded revision prompts in order")
        else:
            print("[generate] next action: run the prompt in the current Claude session, then run validation")
        return 0

    if args.profile == "production":
        sidecar_errors = validate_sidecars(
            output_dir,
            ("qualitative_evidence.json", "qualitative_argument_map.json"),
        )
        if sidecar_errors:
            print("[generate] production sidecars must be created and validated before nested draft generation:")
            for error in sidecar_errors:
                print(f"- {error}")
            return 2

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

    consistency = subprocess.run(consistency_argv, text=True, check=False)
    print(f"[generate] consistency audit exit code: {consistency.returncode}")
    if consistency.returncode == 2:
        print(f"[generate] consistency audit failed: inspect {consistency_path}")
        return 2
    if consistency.returncode == 1:
        print(f"[generate] advisory numeric conflicts found: inspect {consistency_path}")

    validation = subprocess.run(validation_argv, text=True, check=False)
    print(f"[generate] validation exit code: {validation.returncode}")
    if validation.returncode == 0 and args.profile == "production":
        provenance = write_provenance(output_dir, target_output)
        print(f"[generate] provenance: {provenance}")
        audit_errors = validate_sidecars(output_dir, ("qualitative_content_audit.json",))
        if audit_errors:
            print("[generate] report is not production-final until independent content audit is valid:")
            for error in audit_errors:
                print(f"- {error}")
            return 2
        audit = __import__("json").loads(
            (output_dir / "qualitative_content_audit.json").read_text(encoding="utf-8")
        )
        if audit["decision"] != "pass":
            print("[generate] semantic content audit requires bounded revision")
            return 1
        html_output = target_output.with_suffix(".html")
        render_argv = [
            "python",
            str(project_root / "scripts" / "report_to_html.py"),
            "--input",
            str(target_output),
            "--output",
            str(html_output),
            "--standalone",
        ]
        render = subprocess.run(render_argv, text=True, check=False)
        print(f"[generate] HTML render exit code: {render.returncode}")
        if render.returncode != 0:
            return render.returncode
        dom_argv = [
            "python",
            str(project_root / "scripts" / "validate_report_html.py"),
            "--html",
            str(html_output),
            "--markdown",
            str(target_output),
            "--manifest",
            str(output_dir / "render_manifest.json"),
        ]
        dom = subprocess.run(dom_argv, text=True, check=False)
        print(f"[generate] HTML DOM validation exit code: {dom.returncode}")
        if dom.returncode != 0:
            return dom.returncode
    return validation.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
