from validate_report_html import validate_html


def test_html_validator_requires_typed_open_moat_components_and_clean_text():
    markdown = """## 维度一
## 维度二
## 维度三
## 维度四
## 维度五
## 维度六
"""
    html = """<html><body>
<h2>维度一</h2><h2>维度二</h2><h2>维度三</h2>
<h2>维度四</h2><h2>维度五</h2><h2>维度六</h2>
<details data-component-role="moat-interrogation" open></details>
<details data-component-role="moat-falsification" open></details>
</body></html>"""
    errors, manifest = validate_html(html, markdown)
    assert errors == []
    assert manifest["validation"]["dimension_count"] == 6
    assert manifest["schema_version"] == "1.1"
    assert manifest["validation"]["dimension_headings_match"] is True
    assert manifest["source_structure"]["h2_count"] == 6


def test_html_validator_rejects_raw_source_tag_and_closed_moat_table():
    markdown = "\n".join(f"## 维度{x}" for x in "一二三四五六")
    html = """<html><body>
<h2>维度一</h2><h2>维度二</h2><h2>维度三</h2>
<h2>维度四</h2><h2>维度五</h2><h2>维度六</h2>
<p>[src: 年报P.21]</p>
<details data-component-role="moat-interrogation"></details>
<details data-component-role="moat-falsification" open></details>
</body></html>"""
    errors, _ = validate_html(html, markdown)
    assert any("raw Markdown" in error for error in errors)
    assert any("moat-interrogation" in error for error in errors)


def test_html_validator_rejects_dimension_heading_drift():
    markdown = "\n".join(f"## 维度{x}" for x in "一二三四五六")
    html = """<html><body>
<h2>维度二</h2><h2>维度一</h2><h2>维度三</h2>
<h2>维度四</h2><h2>维度五</h2><h2>维度六</h2>
<details data-component-role="moat-interrogation" open></details>
<details data-component-role="moat-falsification" open></details>
</body></html>"""
    errors, manifest = validate_html(html, markdown)
    assert any("headings or order" in error for error in errors)
    assert manifest["validation"]["dimension_headings_match"] is False


def test_html_validator_current_contract_requires_six_core_charts():
    markdown = "\n".join(f"## 维度{x}" for x in "一二三四五六") + "\nanalysis_contract_version: 2.1\n"
    html = """<html><body>
<h2>维度一</h2><h2>维度二</h2><h2>维度三</h2>
<h2>维度四</h2><h2>维度五</h2><h2>维度六</h2>
<details data-component-role="moat-interrogation" open></details>
<details data-component-role="moat-falsification" open></details>
</body></html>"""
    errors, manifest = validate_html(html, markdown)
    assert any("exactly 6 core charts" in error for error in errors)
    assert manifest["validation"]["golden_chart_count"] is False


def test_html_validator_rejects_chart_unit_or_role_drift_from_metadata():
    markdown = "\n".join(f"## 维度{x}" for x in "一二三四五六") + """
chart_ready: true; chart_id: unit-check; chart_type: mixed; x_axis: 年份; bar_series: D&A; line_series: Capex/D&A; unit_map: D&A=亿元, Capex/D&A=倍
"""
    html = """<html><body>
<h2>维度一</h2><h2>维度二</h2><h2>维度三</h2>
<h2>维度四</h2><h2>维度五</h2><h2>维度六</h2>
<details data-component-role="moat-interrogation" open></details>
<details data-component-role="moat-falsification" open></details>
<div class="chart-container" data-chart-id="unit-check" data-chart-series='{"datasets":[{"label":"D&amp;A","unit":"","role":"bar"},{"label":"Capex/D&amp;A","unit":"x","role":"bar"}]}'></div>
</body></html>"""
    errors, manifest = validate_html(html, markdown)
    assert any("unit_map mismatch" in error for error in errors)
    assert any("series role mismatch" in error for error in errors)
    assert manifest["validation"]["chart_metadata_match"] is False
