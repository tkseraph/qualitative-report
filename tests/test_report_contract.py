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
