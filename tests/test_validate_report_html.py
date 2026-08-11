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
