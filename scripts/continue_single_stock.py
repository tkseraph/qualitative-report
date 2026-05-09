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
from pathlib import Path


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


def _validation_command(project_root: Path, target: Path, report_type: str | None = None) -> str:
    command = f"python {project_root / 'scripts' / 'validate_reports.py'} {target}"
    if report_type:
        command += f" --type {report_type}"
    return command


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
        + "必须保留并强化成品报告外壳：Business Quality Verdict / 商业质量总体评级、Quality Snapshot / 质量快照、Executive Summary / 执行摘要、核心矛盾与反证条件、未来观察变量、数据来源与免责声明。\n"
        + "首屏必须让读者快速看懂：商业质量评级、公司本质、护城河来源、最大风险、主要约束、周期位置（如适用）、反证条件。\n"
        + "Business Quality Verdict 后必须提供窄版首屏摘要卡，字段包含：公司本质、商业质量、护城河来源、最大风险、周期位置、反证条件。\n"
        + "D1-D6 每个维度在证据充分时必须以“本章小结”收尾，包含本章结论、最重要证据、观察风险 / 重评触发。\n"
        + "未来观察变量必须包含：当前值 / 本地证据、预警阈值、触发后的重评动作。\n"
        + "微信公众号可读性约束：段落不要过长；正文表格优先 3-5 列，宽表只保留关键列；每张表必须服务一个判断并配有结论句；避免审计式数据堆叠。\n"
        + "结构化参数必须保留，但应标为“结构化参数（机器读取 / 附录）”，放在人工阅读结论、观察变量、数据来源和免责声明之后。\n"
        + "深度总结必须像文章结尾一样组织为：公司本质、为什么优势真实、最大风险、重评触发。\n"
        + f"输出文件：{qualitative_report_path}\n"
        + f"生成后运行验收：{_validation_command(project_root, qualitative_report_path, 'qualitative')}"
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
        prompts = [
            ("step5", output_dir / "step5_qualitative_prompt.md", qualitative_report_path, build_step5_prompt(project_root, output_dir, qualitative_report_path)),
            ("step7", output_dir / "step7_turtle_prompt.md", turtle_report_path, build_step7_prompt(project_root, output_dir, qualitative_report_path, turtle_report_path)),
            ("step8", output_dir / "step8_valuation_prompt.md", valuation_report_path, build_step8_prompt(project_root, output_dir, qualitative_report_path, valuation_report_path)),
        ]
        print("[continue] stage=all")
        print("[continue] checked input files:")
        for path in required:
            print(f"- {path}")
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
    print(f"[continue] prompt file: {prompt_path}")
    print(f"[continue] next target output: {target_output}")
    print(f"\n=== {args.stage} workflow prompt ===")
    print(prompt)


if __name__ == "__main__":
    main()
