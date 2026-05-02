from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_qualitative_prompt_requires_finished_report_shell():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")

    required_sections = [
        "## Business Quality Verdict / 商业质量总体评级",
        "## Quality Snapshot / 质量快照",
        "## Executive Summary / 执行摘要",
        "## 未来观察变量",
        "## 数据来源与免责声明",
    ]

    for section in required_sections:
        assert section in prompt


def test_turtle_report_template_requires_finished_report_shell():
    template = read_text("strategies/turtle/phase3_valuation.md")

    required_sections = [
        "## Strategy Verdict",
        "## Turtle Snapshot / 核心指标快照",
        "## Executive Summary",
        "## 数据来源与免责",
    ]

    for section in required_sections:
        assert section in template


def test_turtle_coordinator_uses_canonical_report_filenames():
    coordinator = read_text("strategies/turtle/coordinator.md")
    agent_c_prompt = read_text("strategies/turtle/phase3_valuation.md")
    factor_interface = read_text("strategies/turtle/references/factor_interface.md")

    assert "{code_market}_qualitative_report.md" in coordinator
    assert "{code_market}_turtle_report.md" in coordinator
    assert "{output_dir}/{code_market}_qualitative_report.md" in agent_c_prompt
    assert "{output_dir}/{code_market}_turtle_report.md" in agent_c_prompt
    assert "{output_dir}/{code_market}_qualitative_report.md" in factor_interface

    assert "{output_dir}/qualitative_report.md" not in coordinator
    assert "{output_dir}/qualitative_report.md" not in agent_c_prompt
    assert "{output_dir}/qualitative_report.md" not in factor_interface
    assert "{output_dir}/{company}_{code}_分析报告.md" not in coordinator
    assert "{output_dir}/{公司名}_{代码}_分析报告.md" not in agent_c_prompt


def test_valuation_report_template_requires_finished_report_shell():
    template = read_text("strategies/valuation/references/report_template.md")

    required_sections = [
        "## Valuation Verdict / 估值总体判断",
        "## Valuation Snapshot / 估值快照",
        "## Executive Summary",
        "## 数据来源与免责声明",
    ]

    for section in required_sections:
        assert section in template


def test_valuation_coordinator_uses_canonical_report_filenames():
    coordinator = read_text("strategies/valuation/coordinator.md")
    phase2_prompt = read_text("strategies/valuation/phase2_valuation.md")
    template = read_text("strategies/valuation/references/report_template.md")

    assert "{code_market}_qualitative_report.md" in coordinator
    assert "{code_market}_valuation_report.md" in coordinator
    assert "{output_dir}/{code_market}_qualitative_report.md" in phase2_prompt
    assert "{output_dir}/{code_market}_valuation_report.md" in phase2_prompt
    assert "{code_market}_qualitative_report.md" in template

    assert "{output_dir}/qualitative_report.md" not in coordinator
    assert "{output_dir}/qualitative_report.md" not in phase2_prompt
    assert "{output_dir}/{code_market}_{code_market}_qualitative_report.md" not in phase2_prompt
    assert "{output_dir}/{company}_{code}_估值报告.md" not in coordinator
    assert " qualitative_report.md" not in template


def test_readme_active_sections_use_three_canonical_report_outputs():
    readme = read_text("README.md")

    assert "{code_market}_qualitative_report.md" in readme
    assert "{code_market}_turtle_report.md" in readme
    assert "{code_market}_valuation_report.md" in readme
    assert "output/{code}_分析报告.md" not in readme
    assert "report.md + report.html" not in readme


def test_active_prompts_and_scripts_avoid_legacy_qualitative_report_name():
    active_paths = [
        "shared/qualitative/coordinator.md",
        "shared/qualitative/coordinator_v2.md",
        "shared/qualitative/qualitative_assessment.md",
        "shared/qualitative/qualitative_assessment_v2.md",
        "shared/qualitative/agents/agent_summary.md",
        "scripts/report_to_html.py",
        "scripts/valuation_engine.py",
    ]

    legacy_pattern = re.compile(r"(?<![\w}])qualitative_report\.md")
    for path in active_paths:
        text = read_text(path)
        assert legacy_pattern.search(text) is None, path
