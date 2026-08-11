"""The generator and validator must consume one canonical report contract."""

from report_contract import report_contract, render_qualitative_prompt_contract
from validate_reports import QUALITATIVE_CONTRACT


def test_qualitative_contract_is_shared_by_generator_and_validator():
    contract = report_contract("qualitative")

    assert QUALITATIVE_CONTRACT is contract
    rendered = render_qualitative_prompt_contract()
    assert contract["d6"]["decision_heading"] in rendered
    assert str(contract["chart_ready"]["minimum_modules"]) in rendered
    assert all(
        field in rendered for field in contract["machine_fields"]
    )


def test_contract_has_versioned_strict_fields():
    contract = report_contract("qualitative")

    assert contract["first_screen_card"]["header"] == ["项目", "结论"]
    assert contract["future_observation"]["priority_tiers"] == ["P0", "P1", "P2"]
    assert set(contract["chart_ready"]["allowed_types"]) == {"line", "bar", "mixed"}
    assert contract["chart_ready"]["routing_metadata"] == ["chart_id", "chart_target"]
    assert contract["business_quality_rating"]["grades"]["B+"]["label"] == "中等偏强"
    assert contract["business_quality_rating"]["grades"]["B"]["label"] == "中等"
    assert contract["business_quality_rating"]["outlooks"] == ["正面", "稳定", "观察", "负面"]
    assert contract["d6"]["modes"] == [
        "not_applicable",
        "diagnostic",
        "listed_asset_bridge",
        "full",
    ]
    assert set(contract["html"]["default_open_table_roles"]) == {
        "moat-interrogation",
        "moat-falsification",
    }


def test_prompt_contract_separates_overall_quality_from_moat_and_names_sotp_modes():
    rendered = render_qualitative_prompt_contract()

    assert "B+ / 中等偏强" in rendered
    assert "护城河评级必须与总体评级分开" in rendered
    assert "diagnostic" in rendered
    assert "重复计价检查" in rendered
