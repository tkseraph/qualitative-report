import json

from qualitative_artifacts import (
    compare_structure_snapshot,
    report_structure_signature,
    validate_current_argument_quality,
    validate_json_artifact,
    write_chain_prompts,
    write_structure_snapshot,
)


def test_write_chain_prompts_separates_evidence_review_and_bounded_revision(tmp_path):
    paths = write_chain_prompts(tmp_path, tmp_path, tmp_path / "report.md")
    assert set(paths) == {
        "step5_evidence_argument_prompt.md",
        "step5_content_review_prompt.md",
        "step5_targeted_revision_prompt.md",
    }
    assert "Do not change the report" in paths["step5_content_review_prompt.md"].read_text()
    revision = paths["step5_targeted_revision_prompt.md"].read_text()
    assert "only headings named" in revision
    assert "existing core chart count" in revision
    assert "qualitative_structure.py" in revision
    assert "--capture" in revision
    assert "--check" in revision


def test_structure_snapshot_rejects_heading_or_chart_routing_drift(tmp_path):
    report = tmp_path / "report.md"
    snapshot = tmp_path / "before.json"
    report.write_text(
        "## 维度一\nchart_ready: true; chart_id: one; chart_target: dimension_1; chart_type: line\n## 维度二\n",
        encoding="utf-8",
    )
    signature = report_structure_signature(report.read_text(encoding="utf-8"))
    assert signature["h2_count"] == 2
    assert signature["chart_count"] == 1
    write_structure_snapshot(report, snapshot)
    assert compare_structure_snapshot(report, snapshot) == []

    report.write_text(
        "## 维度二\nchart_ready: true; chart_id: one; chart_target: dimension_2; chart_type: line\n## 维度一\n",
        encoding="utf-8",
    )
    errors = compare_structure_snapshot(report, snapshot)
    assert any("H2" in error for error in errors)
    assert any("chart" in error for error in errors)


def test_current_argument_quality_requires_two_hypotheses_and_valid_roe_history(tmp_path):
    argument = tmp_path / "qualitative_argument_map.json"
    argument.write_text(json.dumps({"quality_checks": {
        "working_capital_cash_bridge": {"status": "pass", "conclusion": "现金桥已经完成"},
        "competing_moat_hypotheses": [{"name": "单一假说"}],
        "cycle_transmission": {"classification": "弱周期"},
        "roe_history": {"years": 4, "available_years_avg": 20.0, "five_year_avg": 20.0},
        "sotp_economic_separability": {"status": "partial"},
    }}, ensure_ascii=False), encoding="utf-8")
    errors = validate_current_argument_quality(argument)
    assert any("two moat hypotheses" in error for error in errors)
    assert any("five_year_avg must be null" in error for error in errors)


def test_evidence_schema_rejects_unlocated_claim(tmp_path):
    artifact = tmp_path / "qualitative_evidence.json"
    artifact.write_text(json.dumps({
        "schema_version": "1.0",
        "company": "测试股份",
        "as_of": "2025-12-31",
        "evidence": [{
            "id": "E001",
            "claim": "这是一个可验证的公司事实",
            "source_type": "annual_report",
            "source": "年报",
            "locator": "",
            "confidence": "High",
            "scope": "2025",
            "status": "verified"
        }],
        "gaps": []
    }), encoding="utf-8")
    schema = tmp_path.parent / "missing.json"
    real_schema = __import__("qualitative_artifacts").SCHEMA_DIR / "qualitative_evidence_schema.json"
    errors = validate_json_artifact(artifact, real_schema)
    assert any("locator" in error for error in errors)
