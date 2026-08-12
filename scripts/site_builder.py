#!/usr/bin/env python3
"""Build the curated static research-report website."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import shutil
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    from .site_security import inspect_public_tree, load_known_local_secrets
except ImportError:  # pragma: no cover - direct script execution
    from site_security import inspect_public_tree, load_known_local_secrets


CATEGORY_DEFINITIONS = (
    (
        "qualitative",
        "商业质量",
        "从商业模式、护城河、治理和现金转化出发，回答公司是否值得长期跟踪。",
    ),
    (
        "turtle",
        "投资策略",
        "把商业质量、穿透回报率与风险阈值放进同一套可执行决策框架。",
    ),
    (
        "valuation",
        "估值研究",
        "使用多方法估值、交叉验证和反向估值，明确价格隐含的关键假设。",
    ),
)

REQUIRED_REPORT_FIELDS = {
    "id",
    "company_name",
    "stock_code",
    "report_type",
    "title",
    "summary",
    "analysis_date",
    "published_at",
    "public_path",
    "content_path",
}


class SiteBuildError(ValueError):
    """Raised when site source data is incomplete or unsafe."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SiteBuildError(f"Missing site source file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SiteBuildError(f"Invalid JSON in {path}: {exc}") from exc


def load_site_config(site_root: Path) -> dict[str, str]:
    config = _read_json(site_root / "config.json")
    if not isinstance(config, dict):
        raise SiteBuildError("site/config.json must contain a JSON object")
    required = {
        "site_name",
        "registered_site_name",
        "site_tagline",
        "site_description",
        "base_url",
        "icp_number",
    }
    missing = sorted(required - set(config))
    if missing:
        raise SiteBuildError(f"site/config.json missing fields: {', '.join(missing)}")
    normalized = {str(key): str(value) for key, value in config.items()}
    normalized["base_url"] = normalized["base_url"].rstrip("/")
    return normalized


def load_report_manifest(site_root: Path) -> list[dict[str, Any]]:
    reports = _read_json(site_root / "content" / "reports.json")
    if not isinstance(reports, list):
        raise SiteBuildError("site/content/reports.json must contain a JSON array")

    ids: set[str] = set()
    public_paths: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, report in enumerate(reports):
        if not isinstance(report, dict):
            raise SiteBuildError(f"Report entry {index} must be a JSON object")
        missing = sorted(REQUIRED_REPORT_FIELDS - set(report))
        if missing:
            raise SiteBuildError(f"Report entry {index} missing fields: {', '.join(missing)}")
        if report["report_type"] not in {item[0] for item in CATEGORY_DEFINITIONS}:
            raise SiteBuildError(f"Unsupported report_type: {report['report_type']}")
        if report["id"] in ids:
            raise SiteBuildError(f"Duplicate report id: {report['id']}")
        if report["public_path"] in public_paths:
            raise SiteBuildError(f"Duplicate public_path: {report['public_path']}")
        ids.add(str(report["id"]))
        public_paths.add(str(report["public_path"]))
        normalized.append(dict(report))

    return sorted(
        normalized,
        key=lambda item: (str(item["analysis_date"]), str(item["published_at"]), str(item["id"])),
        reverse=True,
    )


def _public_url(public_path: str) -> str:
    path = public_path.strip("/")
    if path.endswith("/index.html"):
        return path[: -len("index.html")]
    return path


PUBLIC_COMPLIANCE_CSS = """.publication-shell-brand>span{display:flex;flex-direction:column;gap:1px}.publication-shell-brand small{color:rgba(244,241,233,.56);font-size:9px;font-weight:400;letter-spacing:.04em}.publication-compliance{padding:32px 24px;text-align:center;background:#171916;color:#f4f1e9;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif}.publication-compliance strong,.publication-compliance>span{display:block}.publication-compliance strong{font-family:'Songti SC','STSong',serif;font-size:16px}.publication-compliance>span,.publication-compliance p{margin:6px 0 0;color:rgba(244,241,233,.64);font-size:11px;line-height:1.7}.publication-compliance .publication-copyright{margin-top:8px;color:rgba(244,241,233,.68)}.publication-records{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px 20px;margin-top:10px}.publication-records a,.publication-records span{display:inline-flex;align-items:center;margin:0;color:rgba(244,241,233,.64);font-size:11px;line-height:1.7}.publication-compliance .public-security-record{gap:6px}.publication-compliance .public-security-record img{width:18px;height:20px;object-fit:contain;flex:0 0 auto}@media(max-width:640px){.publication-records{gap:8px 16px}}"""


def _report_absolute_url(config: dict[str, str], public_path: str) -> str:
    base_url = config.get("base_url", "")
    return urljoin(f"{base_url.rstrip('/')}/", _public_url(public_path)) if base_url else ""


def _prepare_public_report(
    source_html: str,
    *,
    config: dict[str, str],
    report: dict[str, Any],
) -> str:
    """Refresh site-level identity, public metadata, and legal information."""
    cleaned = re.sub(r"\s*<link\s+rel=[\"']canonical[\"'][^>]*>\s*", "\n", source_html, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+property=[\"']og:url[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+property=[\"']og:site_name[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+name=[\"']application-name[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+name=[\"']robots[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s*<style\s+id=[\"']publication-compliance-style[\"'][^>]*>.*?</style>\s*",
        "\n",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )
    cleaned = re.sub(
        r"\s*<section\s+class=[\"']publication-compliance[\"'][^>]*>.*?</section>\s*",
        "\n",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    registered_name = config["registered_site_name"]
    site_name = config["site_name"]

    def update_title(match: re.Match[str]) -> str:
        title = match.group(1).strip()
        suffix = f" · {registered_name} · {site_name}"
        return f"<title>{title if registered_name in title else title + suffix}</title>"

    cleaned = re.sub(r"<title>(.*?)</title>", update_title, cleaned, count=1, flags=re.IGNORECASE | re.DOTALL)

    canonical = _report_absolute_url(config, str(report["public_path"]))
    metadata_tags = [
        f'<meta name="application-name" content="{html_lib.escape(registered_name, quote=True)}">',
        f'<meta property="og:site_name" content="{html_lib.escape(registered_name, quote=True)}">',
    ]
    if canonical:
        metadata_tags.extend(
            (
                f'<link rel="canonical" href="{html_lib.escape(canonical, quote=True)}">',
                f'<meta property="og:url" content="{html_lib.escape(canonical, quote=True)}">',
                '<meta name="robots" content="index,follow">',
            )
        )
    else:
        metadata_tags.append('<meta name="robots" content="noindex,nofollow">')
    metadata_tags.append(f'<style id="publication-compliance-style">{PUBLIC_COMPLIANCE_CSS}</style>')
    if not re.search(r"</head>", cleaned, re.IGNORECASE):
        raise SiteBuildError(f"Published report has no closing head tag: {report['public_path']}")
    cleaned = re.sub(
        r"</head>",
        "\n".join(metadata_tags) + "\n</head>",
        cleaned,
        count=1,
        flags=re.IGNORECASE,
    )

    brand = f"{html_lib.escape(site_name)}<small>{html_lib.escape(registered_name)}</small>"
    cleaned = re.sub(
        r'(<a\s+class=[\"\']publication-shell-brand[\"\'][^>]*>\s*<i>.*?</i>\s*<span>).*?(</span>\s*</a>)',
        lambda match: match.group(1) + brand + match.group(2),
        cleaned,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )

    legal_links = ""
    if config.get("public_security_number"):
        number = html_lib.escape(config["public_security_number"])
        public_security_url = config.get("public_security_url", "")
        public_security_icon = config.get("public_security_icon", "")
        icon = (
            f'<img src="{html_lib.escape(public_security_icon, quote=True)}" alt="" width="18" height="20">'
            if public_security_icon
            else ""
        )
        if public_security_url:
            legal_links += (
                f'<a class="public-security-record" href="{html_lib.escape(public_security_url, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">{icon}{number}</a>'
            )
        else:
            legal_links += f"<span>{number}</span>"
    if config.get("icp_number"):
        legal_links += (
            '<a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">'
            f'{html_lib.escape(config["icp_number"])}</a>'
        )
    compliance = (
        '<section class="publication-compliance" aria-label="网站备案与内容说明">'
        f'<strong>{html_lib.escape(registered_name)}</strong>'
        f'<span>{html_lib.escape(site_name)}</span>'
        '<p>个人非经营性研究记录，不提供证券投资咨询或交易服务；内容不构成任何投资建议。</p>'
        '<p class="publication-copyright">版权所有：网站主办者</p>'
        f'<div class="publication-records">{legal_links}</div></section>'
    )
    bottom_return_pattern = r'(<div\s+class=["\']publication-return["\'][^>]*>.*?</div>)'
    if re.search(bottom_return_pattern, cleaned, re.IGNORECASE | re.DOTALL):
        cleaned = re.sub(
            bottom_return_pattern,
            lambda match: match.group(1) + "\n" + compliance,
            cleaned,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )
    elif re.search(r"</body>", cleaned, re.IGNORECASE):
        cleaned = re.sub(r"</body>", compliance + "\n</body>", cleaned, count=1, flags=re.IGNORECASE)
    else:
        raise SiteBuildError(f"Published report has no closing body tag: {report['public_path']}")
    return "\n".join(line.rstrip() for line in cleaned.splitlines()) + "\n"


def _prepare_reports(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for source in reports:
        report = dict(source)
        report["public_url"] = _public_url(str(report["public_path"]))
        report["search_text"] = " ".join(
            str(report.get(field, ""))
            for field in ("company_name", "stock_code", "title", "summary", "industry", "verdict")
        ).lower()
        prepared.append(report)
    return prepared


def _render_index(site_root: Path, config: dict[str, str], reports: list[dict[str, Any]]) -> str:
    env = Environment(
        loader=FileSystemLoader(site_root / "templates"),
        autoescape=select_autoescape(("html", "xml")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("index.html")
    prepared = _prepare_reports(reports)
    categories = [
        {
            "key": key,
            "label": label,
            "description": description,
            "reports": [item for item in prepared if item["report_type"] == key],
        }
        for key, label, description in CATEGORY_DEFINITIONS
    ]
    latest = prepared[0] if prepared else {}
    latest_date = str(latest.get("analysis_date", ""))
    return template.render(
        config=config,
        reports=prepared,
        categories=categories,
        company_count=len({item["stock_code"] for item in prepared}),
        latest_company=latest.get("company_name", ""),
        latest_date_short=latest_date[5:].replace("-", ".") if len(latest_date) >= 10 else "—",
        build_date=date.today().isoformat(),
    )


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_sitemap(config: dict[str, str], reports: list[dict[str, Any]]) -> str:
    base_url = config.get("base_url", "")
    if not base_url:
        return ""
    urls = [(f"{base_url}/", date.today().isoformat())]
    for report in reports:
        urls.append((urljoin(f"{base_url}/", _public_url(str(report["public_path"]))), report["published_at"]))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for location, last_modified in urls:
        lines.extend(("  <url>", f"    <loc>{location}</loc>", f"    <lastmod>{last_modified}</lastmod>", "  </url>"))
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_site(
    project_root: Path,
    *,
    output_dir: Path | None = None,
    audit_secrets: bool = True,
) -> Path:
    project_root = project_root.resolve()
    site_root = project_root / "site"
    output_dir = (output_dir or site_root / "dist").resolve()
    config = load_site_config(site_root)
    reports = load_report_manifest(site_root)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent))
    try:
        shutil.copytree(site_root / "assets", staging / "assets")
        content_root = site_root / "content"
        for report in reports:
            source = content_root / str(report["content_path"])
            if not source.is_file():
                raise SiteBuildError(f"Missing approved report artifact: {source}")
            destination = staging / str(report["public_path"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                _prepare_public_report(
                    source.read_text(encoding="utf-8"),
                    config=config,
                    report=report,
                ),
                encoding="utf-8",
            )

        (staging / "index.html").write_text(_render_index(site_root, config, reports), encoding="utf-8")
        public_manifest = [
            {key: value for key, value in report.items() if key != "content_path"}
            for report in _prepare_reports(reports)
        ]
        _write_json(staging / "reports.json", public_manifest)

        if config.get("base_url"):
            (staging / "robots.txt").write_text(
                f"User-agent: *\nAllow: /\nSitemap: {config['base_url']}/sitemap.xml\n",
                encoding="utf-8",
            )
            (staging / "sitemap.xml").write_text(_build_sitemap(config, reports), encoding="utf-8")
        else:
            (staging / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

        if audit_secrets:
            findings = inspect_public_tree(staging, known_secrets=load_known_local_secrets(project_root))
            if findings:
                rendered = "; ".join(f"{path}: {', '.join(issues)}" for path, issues in findings.items())
                raise SiteBuildError(f"Public output safety audit failed: {rendered}")
        if output_dir.exists():
            shutil.rmtree(output_dir)
        staging.replace(output_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the curated static research-report website")
    parser.add_argument(
        "--output",
        default=None,
        help="Build directory (default: site/dist)",
    )
    parser.add_argument(
        "--skip-secret-audit",
        action="store_true",
        help="Skip local secret matching (not recommended)",
    )
    args = parser.parse_args(argv)
    project_root = Path(__file__).resolve().parent.parent
    output = build_site(
        project_root,
        output_dir=Path(args.output) if args.output else None,
        audit_secrets=not args.skip_secret_audit,
    )
    print(f"Site built: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
