#!/usr/bin/env python3
"""Semi-automatic single-stock runner v1.

Runs the deterministic parts of the single-stock flow:
- validate inputs
- normalize output directory
- copy annual report PDF into output directory
- run tushare_collector.py
- run pdf_preprocessor.py
- run valuation_engine.py

Then prints standard prompts for the workflow-driven steps:
- qualitative report generation
- final valuation report assembly
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from config import validate_stock_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic single-stock pipeline steps")
    parser.add_argument("--code", required=True, help="Stock code, e.g. 000538.SZ")
    parser.add_argument("--pdf", required=True, help="Path to annual report PDF")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: output/{code})")
    parser.add_argument("--html", action="store_true", help="Reserved for future use; HTML is not part of v1 main flow")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent

    ts_code = validate_stock_code(args.code)
    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise SystemExit(f"Expected a PDF file: {pdf_path}")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else project_root / "output" / ts_code.replace('.', '_')
    output_dir.mkdir(parents=True, exist_ok=True)

    annual_report_path = output_dir / "annual_report.pdf"
    if pdf_path != annual_report_path:
        shutil.copy2(pdf_path, annual_report_path)

    python_bin = sys.executable
    if args.html:
        print("[info] --html is reserved in v1 and is not executed as part of the main flow.")

    print(f"[runner] code={ts_code}")
    print(f"[runner] output_dir={output_dir}")
    print(f"[runner] annual_report={annual_report_path}")

    data_pack_path = output_dir / "data_pack_market.md"
    pdf_sections_path = output_dir / "pdf_sections.json"
    data_pack_report_path = output_dir / "data_pack_report.md"
    valuation_output_path = output_dir / "valuation_computed.md"

    run_cmd([
        python_bin,
        str(project_root / "scripts" / "tushare_collector.py"),
        "--code", ts_code,
        "--output", str(data_pack_path),
    ], cwd=project_root)

    run_cmd([
        python_bin,
        str(project_root / "scripts" / "pdf_preprocessor.py"),
        "--pdf", str(annual_report_path),
        "--output", str(pdf_sections_path),
        "--verbose",
    ], cwd=project_root)

    try:
        run_cmd([
            python_bin,
            str(project_root / "scripts" / "build_data_pack_report.py"),
            "--output-dir", str(output_dir),
        ], cwd=project_root)
        print(f"[runner] data_pack_report generated: {data_pack_report_path}")
    except SystemExit as e:
        print(f"[runner] WARNING: data_pack_report generation failed ({e}); continuing without report-pack")

    run_cmd([
        python_bin,
        str(project_root / "scripts" / "valuation_engine.py"),
        "--code", ts_code,
        "--output-dir", str(output_dir),
    ], cwd=project_root)

    qualitative_inputs = [
        f"- {data_pack_path}",
        f"- {annual_report_path}",
        f"- {pdf_sections_path}",
    ]
    if data_pack_report_path.exists():
        qualitative_inputs.append(f"- {data_pack_report_path}")

    valuation_inputs = [
        f"- {data_pack_path}",
        f"- {output_dir / 'qualitative_report.md'}",
        f"- {valuation_output_path}",
    ]
    if data_pack_report_path.exists():
        valuation_inputs.append(f"- {data_pack_report_path}")

    step5_prompt = (
        "请基于以下输入生成 qualitative_report.md：\n"
        + "\n".join(qualitative_inputs)
        + "\n\n"
        + f"并严格按以下 workflow/reference 文件执行：\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'coordinator_v2.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'qualitative_assessment_v2.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'judgment_examples.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'framework_guide.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'references' / 'output_schema.md'}\n"
        + f"- {project_root / 'shared' / 'qualitative' / 'agents' / 'writing_style.md'}\n\n"
        + f"输出文件：{output_dir / 'qualitative_report.md'}"
    )
    step7_prompt = (
        "在以下文件齐备后生成最终估值报告：\n"
        + "\n".join(valuation_inputs)
        + "\n\n"
        + f"并严格按以下 workflow/reference 文件执行：\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'coordinator.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'phase2_valuation.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'references' / 'valuation_methods.md'}\n"
        + f"- {project_root / 'strategies' / 'valuation' / 'references' / 'report_template.md'}\n\n"
        + f"输出文件建议：{output_dir / (ts_code.replace('.', '_') + '_估值报告.md')}"
    )

    step5_prompt_path = output_dir / "step5_qualitative_prompt.md"
    step7_prompt_path = output_dir / "step7_valuation_prompt.md"
    step5_prompt_path.write_text(step5_prompt + "\n", encoding="utf-8")
    step7_prompt_path.write_text(step7_prompt + "\n", encoding="utf-8")

    print("\n=== Step 5 workflow prompt ===")
    print(step5_prompt)
    print(f"[runner] saved: {step5_prompt_path}")

    print("\n=== Step 7 workflow prompt ===")
    print(step7_prompt)
    print(f"[runner] saved: {step7_prompt_path}")

    return


if __name__ == "__main__":
    main()
