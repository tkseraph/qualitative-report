import json

from qualitative_preflight import audit_inputs


def _write_inputs(output_dir):
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.7\nannual report")
    (output_dir / "data_pack_market.md").write_text("market", encoding="utf-8")
    (output_dir / "computed_metrics.md").write_text("metrics", encoding="utf-8")
    sections = {"metadata": {"section_diagnostics": {}}}
    for section in ("P2", "P3", "P4", "P6", "P13", "MDA", "SUB"):
        sections[section] = f"--- p.10 ---\n{section} " + "usable annual report text " * 3
    (output_dir / "pdf_sections.json").write_text(json.dumps(sections), encoding="utf-8")
    notes = ["> 提取方式：预定位 + 年报原页复核"]
    for index, section in enumerate(("P2", "P3", "P4", "P6", "P13", "SUB"), start=10):
        notes.extend([f"## {section}. note", f"（来源：年报 PDF p.{index}）"])
    (output_dir / "data_pack_report.md").write_text("\n".join(notes), encoding="utf-8")
    (output_dir / "peer_evidence.md").write_text(
        """| Peer | Metric | Confidence |
|---|---|---|
| 蒙牛集团 | 收入 | High |
| 光明乳业股份 | 收入 | High |
| 蒙牛集团 | ROE | High |
| 光明乳业股份 | ROE | High |
## Evidence Gaps
口径不同。
""",
        encoding="utf-8",
    )


def test_production_preflight_passes_audited_inputs_with_legacy_warning(tmp_path):
    _write_inputs(tmp_path)
    audit = audit_inputs(tmp_path)
    assert audit["status"] == "pass"
    assert any(issue["code"] == "legacy_pdf_sections" for issue in audit["issues"])


def test_production_preflight_rejects_unaudited_note_pack(tmp_path):
    _write_inputs(tmp_path)
    notes = tmp_path / "data_pack_report.md"
    notes.write_text(notes.read_text(encoding="utf-8").replace("年报原页复核", "自动生成"), encoding="utf-8")
    audit = audit_inputs(tmp_path)
    assert audit["status"] == "fail"
    assert any(issue["code"] == "unaudited_note_pack" for issue in audit["issues"])
