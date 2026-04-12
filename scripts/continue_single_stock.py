#!/usr/bin/env python3
"""Continue single-stock workflow from existing output_dir.

Supported stages:
- step5: prepare qualitative analysis workflow prompt
- step7: prepare final valuation assembly workflow prompt
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare workflow continuation prompts")
    parser.add_argument("--output-dir", required=True, help="Existing output directory")
    parser.add_argument("--stage", required=True, choices=["step5", "step7"], help="Continuation stage")
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")


def detect_code_prefix(output_dir: Path) -> str:
    data_pack_path = output_dir / "data_pack_market.md"
    text = data_pack_path.read_text(encoding="utf-8")
    code_match = re.search(r"股票代码\s*\|\s*(\S+)", text)
    if not code_match:
        raise SystemExit(f"Unable to determine stock code from: {data_pack_path}")
    return code_match.group(1).strip().replace('.', '_')


def build_step5_prompt(project_root: Path, output_dir: Path, qualitative_report_path: Path) -> str:
    inputs = [
        f"- {output_dir / 'data_pack_market.md'}",
        f"- {output_dir / 'annual_report.pdf'}",
        f"- {output_dir / 'pdf_sections.json'}",
    ]
    data_pack_report = output_dir / 'data_pack_report.md'
    if data_pack_report.exists():
        inputs.append(f"- {data_pack_report}")
    return (
        f"请基于以下输入生成 {qualitative_report_path.name}：\n"
        + "\n".join(inputs)
        + "\n\n"
        + f"并严格按以下 workflow/reference 文件执行：\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'coordinator_v2.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'qualitative_assessment_v2.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'judgment_examples.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'framework_guide.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'output_schema.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'agents' / 'writing_style.md'}\n\n"
        + f"输出文件：{qualitative_report_path}"
    )


def build_step7_prompt(project_root: Path, output_dir: Path, qualitative_report_path: Path, valuation_report_path: Path) -> str:
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
        + f"输出文件建议：{valuation_report_path}"
    )


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not output_dir.exists():
        raise SystemExit(f"Output directory not found: {output_dir}")

    code_prefix = detect_code_prefix(output_dir)
    qualitative_report_path = output_dir / f"{code_prefix}_qualitative_report.md"
    valuation_report_path = output_dir / f"{code_prefix}_valuation_report.md"

    if args.stage == "step5":
        required = [
            output_dir / "data_pack_market.md",
            output_dir / "annual_report.pdf",
            output_dir / "pdf_sections.json",
        ]
        for path in required:
            require_file(path)
        prompt_path = output_dir / "step5_qualitative_prompt.md"
        target_output = qualitative_report_path
        prompt = build_step5_prompt(project_root, output_dir, qualitative_report_path)
    else:
        required = [
            output_dir / "data_pack_market.md",
            qualitative_report_path,
            output_dir / "valuation_computed.md",
        ]
        for path in required:
            require_file(path)
        prompt_path = output_dir / "step7_valuation_prompt.md"
        target_output = valuation_report_path
        prompt = build_step7_prompt(project_root, output_dir, qualitative_report_path, valuation_report_path)

    prompt_path.write_text(prompt + "\n", encoding="utf-8")

    print(f"[continue] stage={args.stage}")
    print("[continue] checked input files:")
    for path in required:
        print(f"- {path}")
    print(f"[continue] prompt file: {prompt_path}")
    print(f"[continue] next target output: {target_output}")
    print(f"\n=== {args.stage} workflow prompt ===")
    print(prompt)


if __name__ == "__main__":
    main()
