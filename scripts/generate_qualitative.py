#!/usr/bin/env python3
"""Observable local entry point for qualitative report generation."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

try:
    from .qualitative_artifacts import (
        compare_structure_snapshot,
        validate_current_argument_quality,
        validate_sidecars,
        write_chain_prompts,
        write_provenance,
        write_structure_snapshot,
    )
    from .qualitative_preflight import audit_inputs, write_manifest
except ImportError:
    from qualitative_artifacts import (
        compare_structure_snapshot,
        validate_current_argument_quality,
        validate_sidecars,
        write_chain_prompts,
        write_provenance,
        write_structure_snapshot,
    )
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
    parser.add_argument(
        "--run-nested-claude",
        action="store_true",
        help=(
            "Call claude -p from this script; production runs evidence/argument, draft, "
            "independent review, bounded revision, re-audit, validation and HTML rendering"
        ),
    )
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


def _run_model_stage(prompt_path: Path, log_path: Path, stage: str) -> int:
    command = _model_command(prompt_path)
    print(f"[generate] model stage={stage}")
    print(f"[generate] model command: {_format_command(command)} < {prompt_path}")
    print(f"[generate] model log: {log_path}")
    with prompt_path.open("r", encoding="utf-8") as prompt_file, log_path.open(
        "w", encoding="utf-8"
    ) as log_file:
        process = subprocess.run(
            command,
            stdin=prompt_file,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    print(f"[generate] model stage={stage} exit code: {process.returncode}")
    return process.returncode


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
        evidence_exit = _run_model_stage(
            chain_prompts["step5_evidence_argument_prompt.md"],
            output_dir / "generate_qualitative_evidence.log",
            "evidence_argument",
        )
        if evidence_exit != 0:
            return evidence_exit
        sidecar_errors = validate_sidecars(
            output_dir,
            ("qualitative_evidence.json", "qualitative_argument_map.json"),
        )
        sidecar_errors.extend(
            validate_current_argument_quality(
                output_dir / "qualitative_argument_map.json"
            )
        )
        if sidecar_errors:
            print("[generate] production evidence/argument sidecars failed validation:")
            for error in sidecar_errors:
                print(f"- {error}")
            return 2

    draft_exit = _run_model_stage(prompt_path, log_path, "draft")
    if draft_exit != 0:
        return draft_exit
    if not target_output.exists():
        print(f"[generate] failed: target output was not created: {target_output}")
        print(f"[generate] inspect log file: {log_path}")
        return 1

    if args.profile == "production":
        baseline_path = write_structure_snapshot(
            target_output,
            output_dir / "pre_revision_structure.json",
        )
        review_prompt = chain_prompts["step5_content_review_prompt.md"]
        review_exit = _run_model_stage(
            review_prompt,
            output_dir / "generate_qualitative_review.log",
            "independent_review",
        )
        if review_exit != 0:
            return review_exit
        audit_errors = validate_sidecars(output_dir, ("qualitative_content_audit.json",))
        if audit_errors:
            print("[generate] independent content audit failed validation:")
            for error in audit_errors:
                print(f"- {error}")
            return 2
        audit_path = output_dir / "qualitative_content_audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit["decision"] == "revise":
            revision_exit = _run_model_stage(
                chain_prompts["step5_targeted_revision_prompt.md"],
                output_dir / "generate_qualitative_revision.log",
                "bounded_revision",
            )
            if revision_exit != 0:
                return revision_exit
            structure_errors = compare_structure_snapshot(target_output, baseline_path)
            if structure_errors:
                for error in structure_errors:
                    print(f"[generate] structure FAIL: {error}")
                return 1
            reaudit_exit = _run_model_stage(
                review_prompt,
                output_dir / "generate_qualitative_reaudit.log",
                "post_revision_review",
            )
            if reaudit_exit != 0:
                return reaudit_exit
            audit_errors = validate_sidecars(output_dir, ("qualitative_content_audit.json",))
            if audit_errors:
                for error in audit_errors:
                    print(f"- {error}")
                return 2
            audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if audit["decision"] != "pass":
            print("[generate] semantic content audit still requires revision")
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
        html_output = target_output.with_suffix(".html")
        render_argv = [
            sys.executable,
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
            sys.executable,
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
        structure_baseline = output_dir / "pre_revision_structure.json"
        if structure_baseline.is_file():
            structure_errors = compare_structure_snapshot(target_output, structure_baseline)
            if structure_errors:
                for error in structure_errors:
                    print(f"[generate] structure FAIL: {error}")
                return 1
        structure_path = write_structure_snapshot(
            target_output,
            output_dir / "report_structure.json",
        )
        print(f"[generate] structure manifest: {structure_path}")
    return validation.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
