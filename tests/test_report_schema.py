from report_schema import REPORT_SCHEMAS


def test_defines_exactly_three_report_types():
    assert set(REPORT_SCHEMAS) == {"qualitative", "turtle", "valuation"}


def test_all_report_schemas_require_shared_finished_page_components():
    for schema in REPORT_SCHEMAS.values():
        requirement_names = {requirement.name for requirement in schema.requirements}
        assert "verdict banner" in requirement_names
        assert "snapshot cards" in requirement_names
        assert "executive summary" in requirement_names
        assert "data sources" in requirement_names
        assert "disclaimer" in requirement_names


def test_qualitative_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["qualitative"].requirements}
    expected = {
        "business quality verdict",
        "quality snapshot",
        "six dimensions",
        "deep summary",
        "future observation variables",
        "structured parameters",
    }
    assert expected.issubset(requirement_names)


def test_turtle_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["turtle"].requirements}
    expected = {
        "strategy verdict",
        "turtle snapshot",
        "owner earnings",
        "penetrating return",
        "safety margin",
        "value-trap filters",
        "thesis card",
        "fundamental stop-loss rules",
        "event monitoring checklist",
    }
    assert expected.issubset(requirement_names)


def test_valuation_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["valuation"].requirements}
    expected = {
        "valuation verdict",
        "valuation snapshot",
        "company classification",
        "method weights",
        "wacc",
        "qualitative adjustments",
        "dcf",
        "pe band",
        "ddm",
        "cross-validation",
        "reverse valuation",
        "valuation range",
    }
    assert expected.issubset(requirement_names)


def test_scope_is_a_share_only():
    for schema in REPORT_SCHEMAS.values():
        assert schema.market_scope == "A-share"
