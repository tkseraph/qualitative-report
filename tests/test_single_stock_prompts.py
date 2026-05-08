from pathlib import Path
import sys

import pytest

from continue_single_stock import build_step5_prompt, build_step7_prompt, build_step8_prompt, main


PROJECT_ROOT = Path("/repo")
OUTPUT_DIR = Path("/repo/output/600018_test")
QUALITATIVE = OUTPUT_DIR / "600018_SH_qualitative_report.md"
TURTLE = OUTPUT_DIR / "600018_SH_turtle_report.md"
VALUATION = OUTPUT_DIR / "600018_SH_valuation_report.md"


def test_step5_prompt_requires_qualitative_shell_and_validation():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert str(QUALITATIVE) in prompt
    assert "Business Quality Verdict / 商业质量总体评级" in prompt
    assert "Quality Snapshot / 质量快照" in prompt
    assert "数据来源与免责声明" in prompt
    assert "python scripts/validate_reports.py" in prompt
    assert "--type qualitative" in prompt


def test_step7_prompt_generates_turtle_report_and_validation():
    prompt = build_step7_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE, TURTLE)

    assert str(QUALITATIVE) in prompt
    assert str(TURTLE) in prompt
    assert "strategies/turtle/coordinator.md" in prompt
    assert "strategies/turtle/phase3_valuation.md" in prompt
    assert "Strategy Verdict" in prompt
    assert "Turtle Snapshot / 核心指标快照" in prompt
    assert "python scripts/validate_reports.py" in prompt
    assert "--type turtle" in prompt


def test_step8_prompt_generates_valuation_report_and_validation():
    prompt = build_step8_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE, VALUATION)

    assert str(QUALITATIVE) in prompt
    assert str(VALUATION) in prompt
    assert "strategies/valuation/coordinator.md" in prompt
    assert "strategies/valuation/phase2_valuation.md" in prompt
    assert "Valuation Verdict / 估值总体判断" in prompt
    assert "Valuation Snapshot / 估值快照" in prompt
    assert "python scripts/validate_reports.py" in prompt
    assert "--type valuation" in prompt


def test_run_single_stock_script_mentions_three_prompt_files_and_directory_validation():
    script = (Path(__file__).resolve().parents[1] / "scripts" / "run_single_stock.py").read_text(encoding="utf-8")

    assert "step5_qualitative_prompt.md" in script
    assert "step7_turtle_prompt.md" in script
    assert "step8_valuation_prompt.md" in script
    assert "validate_reports.py" in script


def test_readme_documents_single_stock_three_report_flow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "run_single_stock.py" in readme
    assert "continue_single_stock.py" in readme
    assert "--stage step5" in readme
    assert "--stage step7" in readme
    assert "--stage step8" in readme
    assert "step5_qualitative_prompt.md" in readme
    assert "step7_turtle_prompt.md" in readme
    assert "step8_valuation_prompt.md" in readme
    assert "validate_reports.py" in readme
    assert "--type qualitative" in readme
    assert "--type turtle" in readme
    assert "--type valuation" in readme


def test_readme_documents_step7_quantitative_prerequisite_behavior():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "phase3_quantitative.md" in readme
    assert "若不存在，请按 turtle coordinator 先生成" in readme
    assert "Step 7 不要求 phase3_quantitative.md 预先存在" in readme


def test_readme_documents_fresh_e2e_acceptance_flow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "最终交付前建议选一个未手工修过的新 A 股样例" in readme
    assert "runner → Step 5 → Step 7 → Step 8 → 目录验收" in readme
    assert "不要只复用已人工补齐的 acceptance 样例" in readme


def test_readme_documents_fixed_acceptance_matrix():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "固定验收矩阵" in readme
    assert "金融 / 银行" in readme
    assert "强周期 / 重资产" in readme
    assert "高研发 / 高资本开支成长制造" in readme
    assert "质量下滑 / 价值陷阱" in readme
    assert "优质但估值不便宜" in readme
    assert "688668_dingtong_e2e_fresh" in readme


def _write_market_pack(output_dir: Path) -> None:
    (output_dir / "data_pack_market.md").write_text("| 股票代码 | 600018.SH |\n", encoding="utf-8")


def _run_continue(output_dir: Path, stage: str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = ["continue_single_stock.py", "--output-dir", str(output_dir), "--stage", stage]
        main()
    finally:
        sys.argv = old_argv


def test_continue_cli_stage5_writes_qualitative_prompt(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")

    _run_continue(output_dir, "step5")

    prompt_path = output_dir / "step5_qualitative_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_qualitative_report.md" in prompt
    assert "--type qualitative" in prompt


def test_continue_cli_stage7_writes_turtle_prompt_without_quantitative_file(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")

    _run_continue(output_dir, "step7")

    prompt_path = output_dir / "step7_turtle_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_turtle_report.md" in prompt
    assert "phase3_quantitative.md" in prompt
    assert "若不存在，请按 turtle coordinator 先生成" in prompt
    assert "--type turtle" in prompt


def test_continue_cli_stage8_writes_valuation_prompt(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")
    (output_dir / "valuation_computed.md").write_text("# computed", encoding="utf-8")

    _run_continue(output_dir, "step8")

    prompt_path = output_dir / "step8_valuation_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_valuation_report.md" in prompt
    assert "Valuation Verdict / 估值总体判断" in prompt
    assert "--type valuation" in prompt


def test_continue_cli_stage8_fails_when_valuation_computed_missing(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        _run_continue(output_dir, "step8")

    assert "Missing required file" in str(exc.value)
    assert "valuation_computed.md" in str(exc.value)


def test_continue_cli_stage_all_writes_three_prompts_and_final_validation(tmp_path, capsys):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")
    (output_dir / "valuation_computed.md").write_text("# computed", encoding="utf-8")

    _run_continue(output_dir, "all")

    assert (output_dir / "step5_qualitative_prompt.md").exists()
    assert (output_dir / "step7_turtle_prompt.md").exists()
    assert (output_dir / "step8_valuation_prompt.md").exists()
    captured = capsys.readouterr()
    assert "Final three-report validation" in captured.out
    assert f"python scripts/validate_reports.py {output_dir.resolve()}" in captured.out


def test_readme_documents_low_friction_local_workflow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "本地低摩擦工作流" in readme
    assert "run_single_stock.py" in readme
    assert "continue_single_stock.py" in readme
    assert "--stage all" in readme
    assert "人工生成三报告" in readme
    assert "目录验收" in readme
