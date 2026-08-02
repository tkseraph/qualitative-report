from site_security import inspect_public_text


def test_public_text_audit_rejects_known_secret_without_echoing_it():
    secret = "example-real-secret-value-123456789"

    findings = inspect_public_text(f"const value = '{secret}'", known_secrets=[secret])

    assert findings == ["known local secret value"]
    assert secret not in " ".join(findings)


def test_public_text_audit_rejects_local_paths_and_upstream_domain():
    findings = inspect_public_text(
        '<link rel="canonical" href="https://terancejiang.com/stock/a">'
        '<p>source: /Users/example/output/report.md</p>'
    )

    assert "macOS user path" in findings
    assert "upstream site URL" in findings


def test_public_text_audit_allows_documented_placeholders():
    findings = inspect_public_text("TUSHARE_TOKEN=your_tushare_token_here")

    assert findings == []


def test_report_contract_requires_html_shell_and_disclaimer():
    findings = inspect_public_text("<p>draft</p>", require_report_contract=True)

    assert "invalid HTML report shell" in findings
    assert "missing investment disclaimer" in findings
