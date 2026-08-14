import json
import shutil
from pathlib import Path

import pytest

from site_builder import SiteBuildError, build_site


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _site_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT / "site", project_root / "site", ignore=shutil.ignore_patterns("dist"))
    (project_root / "site" / "content" / "reports.json").write_text("[]\n", encoding="utf-8")
    return project_root


def test_build_site_writes_categorized_catalog_and_private_robots(tmp_path):
    project_root = _site_project(tmp_path)
    config_path = project_root / "site" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["base_url"] = ""
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

    output = build_site(project_root)

    html = (output / "index.html").read_text(encoding="utf-8")
    assert "<title>小付的笔记 · 价值涌现 · 投研报告目录</title>" in html
    assert "备案网站名称：小付的笔记" in html
    assert "京ICP备202605015号-1" in html
    assert "京公网安备11010602203105号" in html
    assert "https://beian.mps.gov.cn/#/query/webSearch?code=11010602203105" in html
    assert 'class="public-security-record"' in html
    assert 'src="/assets/beian.png"' in html
    assert (output / "assets" / "beian.png").is_file()
    assert "版权所有：网站主办者" in html
    assert "©" not in html
    assert html.index("京公网安备11010602203105号") < html.index("京ICP备202605015号-1")
    assert "研究商业本质" in html
    assert "寻找长期价值" in html
    assert "让价值从证据中" not in html
    assert "让事实沉淀，让价值涌现" in html
    assert "只发布完成复核的版本" not in html
    assert "这里仅收录经过人工复核" not in html
    assert "报告目录" in html
    assert "商业质量" in html
    assert "投资策略" in html
    assert "估值研究" in html
    assert 'content="noindex,nofollow"' in html
    assert (output / "robots.txt").read_text(encoding="utf-8") == "User-agent: *\nDisallow: /\n"


def test_build_site_refreshes_public_report_identity_and_metadata(tmp_path):
    project_root = _site_project(tmp_path)
    site_root = project_root / "site"
    content_path = Path("reports/688187-sh/qualitative/2026-06-18/index.html")
    source = site_root / "content" / content_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "<!doctype html><html><head><title>时代电气</title>"
        '<meta name="robots" content="noindex,nofollow"></head>'
        '<body><div class="publication-shell"><a class="publication-shell-brand" href="#">'
        "<i>研</i><span>价值涌现</span></a></div>"
        '<p>本报告不构成投资建议。</p><div class="publication-return">返回报告目录</div>'
        "</body></html>",
        encoding="utf-8",
    )
    manifest = [
        {
            "id": "688187-sh-qualitative-2026-06-18",
            "company_name": "时代电气",
            "stock_code": "688187.SH",
            "report_type": "qualitative",
            "title": "时代电气报告",
            "summary": "摘要",
            "analysis_date": "2026-06-18",
            "published_at": "2026-08-02",
            "public_path": content_path.as_posix(),
            "content_path": content_path.as_posix(),
        }
    ]
    (site_root / "content" / "reports.json").write_text(json.dumps(manifest), encoding="utf-8")

    output = build_site(project_root)

    detail = (output / content_path).read_text(encoding="utf-8")
    assert "<title>时代电气 · 小付的笔记 · 价值涌现</title>" in detail
    assert 'content="index,follow"' in detail
    assert 'href="https://jiazhiyongxian.cn/reports/688187-sh/qualitative/2026-06-18/"' in detail
    assert "小付的笔记" in detail
    assert "京ICP备202605015号-1" in detail
    assert "京公网安备11010602203105号" in detail
    assert "https://beian.mps.gov.cn/#/query/webSearch?code=11010602203105" in detail
    assert 'class="public-security-record"' in detail
    assert 'src="/assets/beian.png"' in detail
    assert "个人非经营性研究记录" in detail
    assert "版权所有：网站主办者" in detail
    assert "©" not in detail
    assert '<strong class="publication-site-name">价值涌现</strong>' in detail
    assert '<span class="publication-registered-name">小付的笔记</span>' in detail
    assert detail.index('<strong class="publication-site-name">价值涌现</strong>') < detail.index(
        '<span class="publication-registered-name">小付的笔记</span>'
    )
    assert ".publication-compliance .publication-site-name{font-family:'Songti SC','STSong',serif;font-size:18px}" in detail
    assert ".publication-compliance .publication-registered-name" in detail
    assert "font-size:11px" in detail
    assert detail.index("京公网安备11010602203105号") < detail.index("京ICP备202605015号-1")
    assert detail.index('<div class="publication-return">') < detail.index(
        '<section class="publication-compliance"'
    )


def test_build_site_lists_report_title_and_copies_detail_page(tmp_path):
    project_root = _site_project(tmp_path)
    site_root = project_root / "site"
    content_path = Path("reports/688187-sh/qualitative/2026-06-18/index.html")
    source = site_root / "content" / content_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "<!doctype html><html><head><title>时代电气</title></head>"
        "<body>不构成投资建议</body></html>",
        encoding="utf-8",
    )
    manifest = [
        {
            "id": "688187-sh-qualitative-2026-06-18",
            "company_name": "时代电气",
            "stock_code": "688187.SH",
            "report_type": "qualitative",
            "report_type_label": "商业质量评估",
            "title": "时代电气（688187.SH）商业质量评估报告",
            "summary": "高毛利轨交装备与现金转化之间仍需验证。",
            "verdict": "B+ / 较强",
            "industry": "运输设备",
            "exchange": "SSE",
            "analysis_date": "2026-06-18",
            "published_at": "2026-08-02",
            "public_path": content_path.as_posix(),
            "content_path": content_path.as_posix(),
        }
    ]
    (site_root / "content" / "reports.json").write_text(
        json.dumps(manifest, ensure_ascii=False),
        encoding="utf-8",
    )

    output = build_site(project_root)

    index = (output / "index.html").read_text(encoding="utf-8")
    assert "时代电气（688187.SH）商业质量评估报告" in index
    assert "reports/688187-sh/qualitative/2026-06-18/" in index
    assert (output / content_path).is_file()
    public_manifest = json.loads((output / "reports.json").read_text(encoding="utf-8"))
    assert public_manifest[0]["public_url"].endswith("/2026-06-18/")
    assert "content_path" not in public_manifest[0]


def test_build_site_blocks_secret_in_approved_report(tmp_path):
    project_root = _site_project(tmp_path)
    site_root = project_root / "site"
    content_path = Path("reports/688187-sh/qualitative/2026-06-18/index.html")
    source = site_root / "content" / content_path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "<!doctype html><html><head><title>x</title></head>"
        "<body>OPENAI_API_KEY=sk-proj-abcdefghijklmnopqrstuvwxyz123456</body></html>",
        encoding="utf-8",
    )
    manifest = [
        {
            "id": "688187-sh-qualitative-2026-06-18",
            "company_name": "时代电气",
            "stock_code": "688187.SH",
            "report_type": "qualitative",
            "title": "报告",
            "summary": "摘要",
            "analysis_date": "2026-06-18",
            "published_at": "2026-08-02",
            "public_path": content_path.as_posix(),
            "content_path": content_path.as_posix(),
        }
    ]
    (site_root / "content" / "reports.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(SiteBuildError, match="safety audit failed"):
        build_site(project_root)
