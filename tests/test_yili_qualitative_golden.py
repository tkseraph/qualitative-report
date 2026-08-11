import json
from pathlib import Path

from qualitative_quality import canonical_rating
from report_contract import report_contract


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "yili_qualitative_golden.json"


def test_yili_golden_encodes_contract_invariants_not_report_prose():
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    contract = report_contract("qualitative")
    rating = canonical_rating(golden["rating"]["grade"], golden["rating"]["outlook"])

    assert rating.label == golden["rating"]["label"]
    assert rating.display == "B+ / 中等偏强 · 观察"
    assert golden["rating"]["moat_rating"] != golden["rating"]["label"]
    assert golden["default_open_components"] == contract["html"]["default_open_table_roles"]
    assert golden["moat_interrogation"]["row_count"] == 6
    assert golden["sotp"]["mode"] in contract["d6"]["modes"]
    assert "伊利是" not in FIXTURE.read_text(encoding="utf-8")


def test_yili_golden_chart_routing_is_explicit_unique_and_keeps_six_charts():
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    chart_ids = [chart["id"] for chart in golden["charts"]]
    targets = {chart["target"] for chart in golden["charts"]}

    assert len(chart_ids) == report_contract("qualitative")["html"]["golden_core_chart_count"]
    assert len(chart_ids) == len(set(chart_ids))
    assert targets == {"executive_summary", "dimension_1", "dimension_2", "dimension_3"}
