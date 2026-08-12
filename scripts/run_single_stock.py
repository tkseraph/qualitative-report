#!/usr/bin/env python3
"""Semi-automatic single-stock runner v1.

Runs the deterministic parts of the single-stock flow:
- validate inputs
- normalize output directory
- copy annual report PDF into output directory
- run tushare_collector.py
- generate computed_metrics.md
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
from datetime import date
from pathlib import Path

if __package__:
    from .config import validate_stock_code
    from .continue_single_stock import (
        _validation_command,
        build_step5_prompt,
        build_step7_prompt,
        build_step8_prompt,
        prepare_computed_metrics,
    )
else:
    from config import validate_stock_code
    from continue_single_stock import (
        _validation_command,
        build_step5_prompt,
        build_step7_prompt,
        build_step8_prompt,
        prepare_computed_metrics,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic single-stock pipeline steps")
    parser.add_argument("--code", required=True, help="Stock code, e.g. 000538.SZ or 920117.BJ")
    parser.add_argument("--pdf", required=True, help="Path to annual report PDF")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: output/{code})")
    parser.add_argument("--html", action="store_true", help="Reserved for future use; HTML is not part of v1 main flow")
    parser.add_argument("--as-of", default=None, help="Point-in-time boundary (YYYY-MM-DD; default: today)")
    return parser.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> None:
    result = subprocess.run(cmd, cwd=str(cwd))
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent

    ts_code = validate_stock_code(args.code)
    as_of = args.as_of or date.today().isoformat()
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

    code_prefix = ts_code.replace('.', '_')
    data_pack_path = output_dir / "data_pack_market.md"
    pdf_sections_path = output_dir / "pdf_sections.json"
    data_pack_report_path = output_dir / "data_pack_report.md"
    valuation_output_path = output_dir / "valuation_computed.md"
    snapshot_dir = output_dir / "data_snapshot"
    qualitative_report_path = output_dir / f"{code_prefix}_qualitative_report.md"
    turtle_report_path = output_dir / f"{code_prefix}_turtle_report.md"
    valuation_report_path = output_dir / f"{code_prefix}_valuation_report.md"

    run_cmd([
        python_bin,
        str(project_root / "scripts" / "tushare_collector.py"),
        "--code", ts_code,
        "--output", str(data_pack_path),
        "--as-of", as_of,
        "--snapshot-dir", str(snapshot_dir),
    ], cwd=project_root)

    computed_metrics_path = prepare_computed_metrics(output_dir)
    if computed_metrics_path:
        print(f"[runner] computed metrics generated: {computed_metrics_path}")
    else:
        print("[runner] WARNING: computed metrics unavailable; Step 5 will use degraded arithmetic rules")

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
        "--as-of", as_of,
        "--snapshot-dir", str(snapshot_dir),
    ], cwd=project_root)

    step5_prompt = build_step5_prompt(project_root, output_dir, qualitative_report_path)
    step7_prompt = build_step7_prompt(project_root, output_dir, qualitative_report_path, turtle_report_path)
    step8_prompt = build_step8_prompt(project_root, output_dir, qualitative_report_path, valuation_report_path)

    step5_prompt_path = output_dir / "step5_qualitative_prompt.md"
    step7_prompt_path = output_dir / "step7_turtle_prompt.md"
    step8_prompt_path = output_dir / "step8_valuation_prompt.md"
    step5_prompt_path.write_text(step5_prompt + "\n", encoding="utf-8")
    step7_prompt_path.write_text(step7_prompt + "\n", encoding="utf-8")
    step8_prompt_path.write_text(step8_prompt + "\n", encoding="utf-8")

    print("\n=== Step 5 workflow prompt ===")
    print(step5_prompt)
    print(f"[runner] saved: {step5_prompt_path}")

    print("\n=== Step 7 workflow prompt ===")
    print(step7_prompt)
    print(f"[runner] saved: {step7_prompt_path}")

    print("\n=== Step 8 workflow prompt ===")
    print(step8_prompt)
    print(f"[runner] saved: {step8_prompt_path}")

    print("\n=== Final three-report validation ===")
    print(_validation_command(project_root, output_dir))

    return


if __name__ == "__main__":
    main()
