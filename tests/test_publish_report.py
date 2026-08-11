import json
import shutil
from pathlib import Path

import pytest

from publish_report import PublishError, extract_report_metadata, prepare_report_html, publish_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _site_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "site", project_root / "site", ignore=shutil.ignore_patterns("dist"))
    (project_root / "site" / "content" / "reports.json").write_text("[]\n", encoding="utf-8")
    return project_root


def _write_report(tmp_path: Path, *, include_secret: bool = False) -> Path:
    output = tmp_path / "output"
    output.mkdir(parents=True, exist_ok=True)
    report = output / "688187_SH_qualitative_report.html"
    secret = "<p>TUSHARE_TOKEN=abcdefghijklmnopqrstuvxyz123456</p>" if include_secret else ""
    report.write_text(
        "<!doctype html><html lang='zh-CN'><head>"
        "<title>时代电气 (688187.SH) · 商业质量评估</title>"
        "<meta name='description' content='时代电气商业质量研究'>"
        "<link rel='canonical' href='https://terancejiang.com/zh/stock/old.html'>"
        "<meta property='og:url' content='https://terancejiang.com/zh/stock/old.html'>"
        "</head><body><div class='ticker'>SSE · 运输设备 · 688187.SH</div>"
        f"{secret}<p>本报告不构成投资建议。</p></body></html>",
        encoding="utf-8",
    )
    report.with_suffix(".md").write_text(
        "# 时代电气（688187.SH）商业质量评估报告\n\n"
        "**总体评级：B+ / 较强，现金转化风险观察。**\n\n"
        "时代电气以轨道交通电气装备为底盘，向功率半导体和新能源装备延伸，现金转化仍需持续验证。\n",
        encoding="utf-8",
    )
    (output / "data_pack_market.md").write_text("*生成时间: 2026-06-18 15:46:13*\n", encoding="utf-8")
    return report


def test_extract_report_metadata_uses_companion_markdown_and_data_date(tmp_path):
    report = _write_report(tmp_path)

    metadata = extract_report_metadata(report, "qualitative")

    assert metadata["company_name"] == "时代电气"
    assert metadata["stock_code"] == "688187.SH"
    assert metadata["analysis_date"] == "2026-06-18"
    assert metadata["industry"] == "运输设备"
    assert metadata["verdict"] == "B+ / 较强"
    assert "现金转化" in metadata["summary"]


def test_extract_report_metadata_prefers_structured_canonical_quality_rating(tmp_path):
    report = _write_report(tmp_path)
    markdown = report.with_suffix(".md")
    markdown.write_text(
        markdown.read_text(encoding="utf-8")
        + """
## 结构化参数（机器读取 / 附录）
| 参数 | 值 |
|---|---|
| business_quality_grade | B+ |
| business_quality_label | 中等偏强 |
| rating_outlook | 观察 |
| rating_version | 2.0 |
""",
        encoding="utf-8",
    )

    metadata = extract_report_metadata(report, "qualitative")
    assert metadata["verdict"] == "B+ / 中等偏强 · 观察"


def test_prepare_report_html_removes_upstream_metadata_and_adds_catalog_link(tmp_path):
    report = _write_report(tmp_path)
    source = report.read_text(encoding="utf-8")
    metadata = extract_report_metadata(report, "qualitative")

    prepared = prepare_report_html(
        source,
        config={"site_name": "个人投研档案", "base_url": "", "social_image": "/assets/og.png"},
        metadata=metadata,
        public_path="reports/688187-sh/qualitative/2026-06-18/index.html",
    )

    assert "terancejiang.com" not in prepared
    assert 'content="noindex,nofollow"' in prepared
    assert prepared.count("返回报告目录") == 2
    assert 'class="publication-return"' in prepared
    assert "../../../../index.html" in prepared


def test_prepare_report_html_strips_trailing_whitespace(tmp_path):
    report = _write_report(tmp_path)
    source = report.read_text(encoding="utf-8").replace("</body>", "  \n</body>")
    metadata = extract_report_metadata(report, "qualitative")

    prepared = prepare_report_html(
        source,
        config={"site_name": "个人投研档案", "base_url": "", "social_image": "/assets/og.png"},
        metadata=metadata,
        public_path="reports/688187-sh/qualitative/2026-06-18/index.html",
    )

    assert all(line == line.rstrip() for line in prepared.splitlines())


def test_publish_report_requires_approval_before_writing(tmp_path):
    project_root = _site_project(tmp_path)
    report = _write_report(tmp_path)

    entry = publish_report(project_root, report, approve=False)

    assert entry["id"] == "688187-sh-qualitative-2026-06-18"
    assert json.loads((project_root / "site/content/reports.json").read_text(encoding="utf-8")) == []
    assert not (project_root / "site/dist").exists()


def test_publish_report_approves_detail_page_and_builds_catalog(tmp_path):
    project_root = _site_project(tmp_path)
    report = _write_report(tmp_path)

    entry = publish_report(project_root, report, approve=True)

    detail = project_root / "site/dist" / entry["public_path"]
    index = (project_root / "site/dist/index.html").read_text(encoding="utf-8")
    detail_html = detail.read_text(encoding="utf-8")
    assert detail.is_file()
    assert "价值涌现" in detail_html
    assert detail_html.count("返回报告目录") == 2
    assert 'class="publication-return"' in detail_html
    assert entry["title"] in index
    assert "商业质量" in index


def test_publish_report_rejects_credential_before_writing(tmp_path):
    project_root = _site_project(tmp_path)
    report = _write_report(tmp_path, include_secret=True)

    with pytest.raises(PublishError, match="safety audit failed"):
        publish_report(project_root, report, approve=True)

    assert json.loads((project_root / "site/content/reports.json").read_text(encoding="utf-8")) == []
