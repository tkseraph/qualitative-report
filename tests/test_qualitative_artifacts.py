import json

from qualitative_artifacts import validate_json_artifact, write_chain_prompts


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
