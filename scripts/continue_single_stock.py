#!/usr/bin/env python3
"""Continue single-stock workflow from existing output_dir.

Supported stages:
- step5: prepare qualitative analysis workflow prompt
- step7: prepare turtle strategy workflow prompt
- step8: prepare final valuation assembly workflow prompt
- all: refresh all three prompts
"""

from __future__ import annotations

import argparse
import re
import shlex
from pathlib import Path
from string import Template

try:
    from report_contract import render_qualitative_prompt_contract
    from quality_control import main as quality_control_main
except ModuleNotFoundError:  # package import: scripts.continue_single_stock
    from scripts.report_contract import render_qualitative_prompt_contract
    from scripts.quality_control import main as quality_control_main


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare workflow continuation prompts")
    parser.add_argument("--output-dir", required=True, help="Existing output directory")
    parser.add_argument("--stage", required=True, choices=["step5", "step7", "step8", "all"], help="Continuation stage")
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")


def detect_code_prefix(output_dir: Path) -> str:
    data_pack_path = output_dir / "data_pack_market.md"
    text = data_pack_path.read_text(encoding="utf-8") if data_pack_path.exists() else ""
    code_match = re.search(r"股票代码\s*(?:\||[:：])\s*([0-9]{6}[._](?:SH|SZ))", text, re.IGNORECASE)
    if code_match:
        return code_match.group(1).strip().replace('.', '_').upper()
    for pattern in ("*_qualitative_report.md", "*_turtle_report.md", "*_valuation_report.md"):
        for path in sorted(output_dir.glob(pattern)):
            match = re.match(r"(\d{6}_(?:SH|SZ))_", path.name, re.IGNORECASE)
            if match:
                return match.group(1).upper()
    raise SystemExit(f"Unable to determine stock code from: {data_pack_path}")


_STEP5_PROMPT_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "shared"
    / "qualitative"
    / "step5_prompt_template.md"
)


def _validation_argv(
    project_root: Path,
    target: Path,
    report_type: str | None = None,
) -> list[str]:
    """Build a shell-independent report validation argument vector."""
    argv = [
        "python",
        str(project_root / "scripts" / "validate_reports.py"),
        str(target),
    ]
    if report_type:
        argv.extend(["--type", report_type])
    return argv


def _validation_command(
    project_root: Path,
    target: Path,
    report_type: str | None = None,
) -> str:
    """Format validation argv for prompts and terminal display."""
    return shlex.join(_validation_argv(project_root, target, report_type))


def _consistency_argv(project_root: Path, target: Path, output: Path) -> list[str]:
    """Build the advisory cross-passage audit argument vector."""
    return [
        "python",
        str(project_root / "scripts" / "report_consistency.py"),
        "--report",
        str(target),
        "--output",
        str(output),
    ]


def _consistency_command(project_root: Path, target: Path, output: Path) -> str:
    return shlex.join(_consistency_argv(project_root, target, output))


def prepare_computed_metrics(output_dir: Path) -> Path | None:
    """Generate the deterministic Step5 metric budget when the data pack supports it.

    Failure is intentionally non-fatal: older/minimal data packs can still use
    the existing qualitative prompt path, which records the missing budget as a
    quality gap instead of blocking prompt preparation.
    """
    input_path = output_dir / "data_pack_market.md"
    output_path = output_dir / "computed_metrics.md"
    exit_code = quality_control_main([
        "--input",
        str(input_path),
        "--output",
        str(output_path),
    ])
    if exit_code == 0:
        return output_path
    # Never let a failed refresh silently feed an older company's arithmetic
    # budget into a new report run.
    output_path.unlink(missing_ok=True)
    return None


def _render_step5_prompt_template(**values: str) -> str:
    template = Template(_STEP5_PROMPT_TEMPLATE.read_text(encoding="utf-8"))
    return template.substitute(values).rstrip("\n")


def build_step5_prompt(project_root: Path, output_dir: Path, qualitative_report_path: Path) -> str:
    inputs = [
        f"- {output_dir / 'data_pack_market.md'}",
        f"- {output_dir / 'annual_report.pdf'}",
        f"- {output_dir / 'pdf_sections.json'}",
        f"- {output_dir / 'computed_metrics.md'}（若已生成：CM§1-CM§5 直接引用，禁止重复心算）",
    ]
    data_pack_report = output_dir / "data_pack_report.md"
    if data_pack_report.exists():
        inputs.append(f"- {data_pack_report}")
    peer_evidence = output_dir / "peer_evidence.md"
    if peer_evidence.exists():
        inputs.append(f"- {peer_evidence}")

    return _render_step5_prompt_template(
        report_name=qualitative_report_path.name,
        inputs="\n".join(inputs),
        project_root=str(project_root),
        qualitative_contract=render_qualitative_prompt_contract(),
        qualitative_report_path=str(qualitative_report_path),
        validation_command=_validation_command(
            project_root,
            qualitative_report_path,
            "qualitative",
        ),
        consistency_command=_consistency_command(
            project_root,
            qualitative_report_path,
            output_dir / "consistency_report.md",
        ),
        consistency_report_path=str(output_dir / "consistency_report.md"),
    )


def build_step7_prompt(project_root: Path, output_dir: Path, qualitative_report_path: Path, turtle_report_path: Path) -> str:
    inputs = [
        f"- {output_dir / 'data_pack_market.md'}",
        f"- {qualitative_report_path}",
        f"- {output_dir / 'phase3_quantitative.md'}（若不存在，请按 turtle coordinator 先生成）",
    ]
    data_pack_report = output_dir / 'data_pack_report.md'
    if data_pack_report.exists():
        inputs.append(f"- {data_pack_report}")
    return (
        "在以下文件齐备后生成龟龟投资策略报告：\n"
        + "\n".join(inputs)
        + "\n\n"
        + f"并严格按以下 workflow/reference 文件执行：\n"
        + f"- {project_root / 'strategies' / 'turtle' / 'coordinator.md'}\n"
        + f"- {project_root / 'strategies' / 'turtle' / 'phase3_quantitative.md'}\n"
        + f"- {project_root / 'strategies' / 'turtle' / 'phase3_valuation.md'}\n"
        + f"- {project_root / 'strategies' / 'turtle' / 'references' / 'factor_interface.md'}\n\n"
        + "必须保留成品报告外壳：Strategy Verdict、Turtle Snapshot / 核心指标快照、Executive Summary、数据来源与免责。\n"
        + f"输出文件：{turtle_report_path}\n"
        + f"生成后运行验收：{_validation_command(project_root, turtle_report_path, 'turtle')}"
    )


def build_step8_prompt(project_root: Path, output_dir: Path, qualitative_report_path: Path, valuation_report_path: Path) -> str:
    inputs = [
        f"- {output_dir / 'data_pack_market.md'}",
        f"- {qualitative_report_path}",
        f"- {output_dir / 'valuation_computed.md'}",
    ]
    data_pack_report = output_dir / 'data_pack_report.md'
    if data_pack_report.exists():
        inputs.append(f"- {data_pack_report}")
    return (
        "在以下文件齐备后生成最终估值报告：\n"
        + "\n".join(inputs)
        + "\n\n"
        + f"并严格按以下 workflow/reference 文件执行：\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'coordinator.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'phase2_valuation.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'references' / 'valuation_methods.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'references' / 'report_template.md'}\n\n"
        + "必须保留成品报告外壳：Valuation Verdict / 估值总体判断、Valuation Snapshot / 估值快照、Executive Summary、数据来源与免责声明。\n"
        + f"输出文件：{valuation_report_path}\n"
        + f"生成后运行验收：{_validation_command(project_root, valuation_report_path, 'valuation')}"
    )


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not output_dir.exists():
        raise SystemExit(f"Output directory not found: {output_dir}")

    code_prefix = detect_code_prefix(output_dir)
    qualitative_report_path = output_dir / f"{code_prefix}_qualitative_report.md"
    turtle_report_path = output_dir / f"{code_prefix}_turtle_report.md"
    valuation_report_path = output_dir / f"{code_prefix}_valuation_report.md"

    if args.stage == "all":
        required = [
            output_dir / "data_pack_market.md",
            output_dir / "annual_report.pdf",
            output_dir / "pdf_sections.json",
            output_dir / "valuation_computed.md",
        ]
        for path in required:
            require_file(path)
        computed_metrics_path = prepare_computed_metrics(output_dir)
        prompts = [
            ("step5", output_dir / "step5_qualitative_prompt.md", qualitative_report_path, build_step5_prompt(project_root, output_dir, qualitative_report_path)),
            ("step7", output_dir / "step7_turtle_prompt.md", turtle_report_path, build_step7_prompt(project_root, output_dir, qualitative_report_path, turtle_report_path)),
            ("step8", output_dir / "step8_valuation_prompt.md", valuation_report_path, build_step8_prompt(project_root, output_dir, qualitative_report_path, valuation_report_path)),
        ]
        print("[continue] stage=all")
        print("[continue] checked input files:")
        for path in required:
            print(f"- {path}")
        if computed_metrics_path:
            print(f"[continue] computed metrics: {computed_metrics_path}")
        else:
            print("[continue] computed metrics unavailable; Step5 prompt will use degraded arithmetic rules")
        for stage, prompt_path, target_output, prompt in prompts:
            prompt_path.write_text(prompt + "\n", encoding="utf-8")
            print(f"[continue] {stage} prompt file: {prompt_path}")
            print(f"[continue] {stage} target output: {target_output}")
            print(f"\n=== {stage} workflow prompt ===")
            print(prompt)
        print("\n=== Final three-report validation ===")
        print(_validation_command(project_root, output_dir))
        return

    if args.stage == "step5":
        required = [
            output_dir / "data_pack_market.md",
            output_dir / "annual_report.pdf",
            output_dir / "pdf_sections.json",
        ]
        for path in required:
            require_file(path)
        computed_metrics_path = prepare_computed_metrics(output_dir)
        prompt_path = output_dir / "step5_qualitative_prompt.md"
        target_output = qualitative_report_path
        prompt = build_step5_prompt(project_root, output_dir, qualitative_report_path)
    elif args.stage == "step7":
        required = [
            output_dir / "data_pack_market.md",
            qualitative_report_path,
        ]
        for path in required:
            require_file(path)
        prompt_path = output_dir / "step7_turtle_prompt.md"
        target_output = turtle_report_path
        prompt = build_step7_prompt(project_root, output_dir, qualitative_report_path, turtle_report_path)
    else:
        required = [
            output_dir / "data_pack_market.md",
            qualitative_report_path,
            output_dir / "valuation_computed.md",
        ]
        for path in required:
            require_file(path)
        prompt_path = output_dir / "step8_valuation_prompt.md"
        target_output = valuation_report_path
        prompt = build_step8_prompt(project_root, output_dir, qualitative_report_path, valuation_report_path)

    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    print(f"[continue] stage={args.stage}")
    print("[continue] checked input files:")
    for path in required:
        print(f"- {path}")
    if args.stage == "step5":
        if computed_metrics_path:
            print(f"[continue] computed metrics: {computed_metrics_path}")
        else:
            print("[continue] computed metrics unavailable; Step5 prompt will use degraded arithmetic rules")
    print(f"[continue] prompt file: {prompt_path}")
    print(f"[continue] next target output: {target_output}")
    print(f"\n=== {args.stage} workflow prompt ===")
    print(prompt)


if __name__ == "__main__":
    main()
