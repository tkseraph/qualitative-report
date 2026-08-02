#!/usr/bin/env python3
"""Approve one finished HTML report for the local static publication site."""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

try:
    from .site_builder import SiteBuildError, build_site, load_report_manifest, load_site_config
    from .site_security import inspect_public_text, load_known_local_secrets
except ImportError:  # pragma: no cover - direct script execution
    from site_builder import SiteBuildError, build_site, load_report_manifest, load_site_config
    from site_security import inspect_public_text, load_known_local_secrets


REPORT_TYPES = {
    "qualitative": "商业质量评估",
    "turtle": "投资策略报告",
    "valuation": "估值研究报告",
}

PUBLICATION_SHELL_CSS = """
.publication-shell{position:relative;z-index:50;background:#171916;color:#f4f1e9;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;border-bottom:1px solid rgba(255,255,255,.14)}
.publication-shell-inner{max-width:1180px;margin:0 auto;min-height:52px;padding:0 24px;display:flex;align-items:center;justify-content:space-between;gap:18px}
.publication-shell a{color:inherit;text-decoration:none}.publication-shell-brand{display:flex;align-items:center;gap:10px;font-size:13px;font-weight:600;letter-spacing:.04em}.publication-shell-brand i{width:24px;height:24px;display:grid;place-items:center;background:#f4f1e9;color:#171916;font-family:'Songti SC','STSong',serif;font-style:normal}.publication-shell-meta{color:rgba(244,241,233,.62);font-size:11px}.publication-shell-meta a{margin-left:12px;color:#f0b2a8}.publication-return{padding:48px 24px 56px;text-align:center;background:#f4f1e9;border-top:1px solid rgba(23,25,22,.16);font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif}.publication-return a{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:48px;padding:0 24px;background:#171916;color:#f4f1e9!important;text-decoration:none!important;font-size:14px;font-weight:600;letter-spacing:.03em;border:1px solid #171916;transition:background .18s ease,color .18s ease}.publication-return a:hover{background:#a33b2e;border-color:#a33b2e}.publication-return a:focus-visible{outline:3px solid rgba(163,59,46,.3);outline-offset:4px}@media(max-width:640px){.publication-shell-inner{padding:0 14px}.publication-shell-meta span{display:none}.publication-return{padding:36px 16px 44px}.publication-return a{width:100%;max-width:360px}}
""".strip()


class PublishError(ValueError):
    """Raised when a report cannot enter the public site."""


def _strip_tags(value: str) -> str:
    return html_lib.unescape(re.sub(r"<[^>]+>", " ", value)).replace("\xa0", " ").strip()


def _clean_markdown(value: str) -> str:
    value = re.sub(r"[`*_>#]", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _truncate(value: str, limit: int = 150) -> str:
    value = value.strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def _first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else ""


def infer_report_type(path: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    name = path.name.lower()
    for report_type in REPORT_TYPES:
        if f"_{report_type}_report" in name:
            return report_type
    raise PublishError("Cannot infer report type from filename; pass --type")


def _companion_markdown(path: Path) -> str:
    candidate = path.with_suffix(".md")
    if candidate.exists():
        return candidate.read_text(encoding="utf-8", errors="ignore")
    return ""


def _date_from_sibling_data(path: Path) -> str:
    for name in ("data_pack_market.md", "data_pack_report.md"):
        candidate = path.parent / name
        if not candidate.exists():
            continue
        value = _first_match(r"生成时间\s*:\s*(\d{4}-\d{2}-\d{2})", candidate.read_text(encoding="utf-8", errors="ignore"))
        if value:
            return value
    return ""


def extract_report_metadata(
    path: Path,
    report_type: str,
    *,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    source_html = path.read_text(encoding="utf-8")
    markdown = _companion_markdown(path)
    overrides = overrides or {}

    company_name = ""
    stock_code = ""
    markdown_title = _first_match(r"^#\s+(.+)$", markdown, re.MULTILINE)
    title_match = re.search(r"^#\s+(.+?)（([0-9A-Za-z.]+)）", markdown, re.MULTILINE)
    if title_match:
        company_name = title_match.group(1).strip()
        stock_code = title_match.group(2).upper().strip()

    html_title = _strip_tags(_first_match(r"<title>(.*?)</title>", source_html, re.IGNORECASE | re.DOTALL))
    if not company_name or not stock_code:
        html_title_match = re.search(r"(.+?)\s*\(([0-9A-Za-z.]+)\)", html_title)
        if html_title_match:
            company_name = company_name or html_title_match.group(1).strip()
            stock_code = stock_code or html_title_match.group(2).upper().strip()

    if not company_name or not re.fullmatch(r"[0-9A-Z]+\.[A-Z]+", stock_code):
        raise PublishError("Report title must contain company name and stock code such as 688187.SH")

    analysis_date = overrides.get("analysis_date", "")
    if not analysis_date:
        analysis_date = _first_match(r"(?:分析日期|生成时间)[：:\s]+(\d{4}-\d{2}-\d{2})", markdown)
    if not analysis_date:
        analysis_date = _date_from_sibling_data(path)
    if not analysis_date:
        analysis_date = date.today().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", analysis_date):
        raise PublishError("analysis date must use YYYY-MM-DD")

    description = _first_match(
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
        source_html,
        re.IGNORECASE | re.DOTALL,
    )
    summary = overrides.get("summary", "")
    if not summary and markdown:
        rating_end = re.search(r"\*\*(?:总体评级|核心判定)[：:].+?\*\*", markdown)
        body_after_rating = markdown[rating_end.end() :] if rating_end else markdown
        for paragraph in re.split(r"\n\s*\n", body_after_rating):
            cleaned = _clean_markdown(paragraph)
            if cleaned and not cleaned.startswith(("|", "##", "chart_ready:")) and len(cleaned) >= 35:
                summary = cleaned
                break
    summary = _truncate(summary or _strip_tags(description) or f"{company_name}{REPORT_TYPES[report_type]}")

    verdict = overrides.get("verdict", "")
    if not verdict and markdown:
        verdict = _first_match(r"\*\*总体评级[：:]\s*([^*]+?)\*\*", markdown)
        verdict = re.split(r"[，。；;]", verdict)[0].strip()
    if not verdict:
        verdict = _strip_tags(_first_match(r'<span\s+class=["\'][^"\']*tag[^"\']*["\'][^>]*>(.*?)</span>', source_html, re.IGNORECASE | re.DOTALL))

    ticker_line = _strip_tags(_first_match(r'<div\s+class=["\']ticker["\'][^>]*>(.*?)</div>', source_html, re.IGNORECASE | re.DOTALL))
    ticker_parts = [part.strip() for part in ticker_line.split("·")]
    exchange = ticker_parts[0] if len(ticker_parts) >= 2 else ""
    industry = overrides.get("industry", "") or (ticker_parts[-2] if len(ticker_parts) >= 3 else "")

    title = overrides.get("title", "") or _clean_markdown(markdown_title) or html_title
    if report_type == "qualitative" and "商业质量" not in title:
        title = f"{company_name}（{stock_code}）商业质量评估报告"

    return {
        "company_name": company_name,
        "stock_code": stock_code,
        "report_type": report_type,
        "report_type_label": REPORT_TYPES[report_type],
        "title": title,
        "summary": summary,
        "verdict": _truncate(verdict, 46),
        "industry": industry,
        "exchange": exchange,
        "analysis_date": analysis_date,
    }


def _report_url(base_url: str, public_path: str) -> str:
    relative = public_path.strip("/")
    if relative.endswith("index.html"):
        relative = relative[: -len("index.html")]
    return urljoin(f"{base_url.rstrip('/')}/", relative) if base_url else ""


def prepare_report_html(
    source_html: str,
    *,
    config: dict[str, str],
    metadata: dict[str, str],
    public_path: str,
) -> str:
    """Remove upstream metadata and add a platform-level return link."""
    cleaned = re.sub(r"\s*<link\s+rel=[\"']canonical[\"'][^>]*>\s*", "\n", source_html, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+property=[\"']og:url[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*<meta\s+name=[\"']robots[\"'][^>]*>\s*", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\s*<link\s+rel=[\"']preload[\"'][^>]*JetBrainsMono[^>]*>\s*",
        "\n",
        cleaned,
        flags=re.IGNORECASE,
    )

    canonical = _report_url(config.get("base_url", ""), public_path)
    metadata_tags = []
    if canonical:
        metadata_tags.extend(
            (
                f'<link rel="canonical" href="{html_lib.escape(canonical, quote=True)}">',
                f'<meta property="og:url" content="{html_lib.escape(canonical, quote=True)}">',
                '<meta name="robots" content="index,follow">',
            )
        )
        social_image = config.get("social_image", "")
        if social_image:
            image_url = urljoin(f"{config['base_url'].rstrip('/')}/", social_image.lstrip("/"))
            metadata_tags.append(f'<meta property="og:image" content="{html_lib.escape(image_url, quote=True)}">')
    else:
        metadata_tags.append('<meta name="robots" content="noindex,nofollow">')
    metadata_tags.append(f'<style id="publication-shell-style">{PUBLICATION_SHELL_CSS}</style>')
    if "</head>" not in cleaned.lower():
        raise PublishError("Report HTML has no closing head tag")
    cleaned = re.sub(r"</head>", "\n".join(metadata_tags) + "\n</head>", cleaned, count=1, flags=re.IGNORECASE)

    home_href = "../../../../index.html"
    shell = (
        '<div class="publication-shell">'
        '<div class="publication-shell-inner">'
        f'<a class="publication-shell-brand" href="{home_href}"><i>研</i><span>{html_lib.escape(config["site_name"])}</span></a>'
        '<div class="publication-shell-meta">'
        f'<span>{html_lib.escape(metadata["report_type_label"])} · {html_lib.escape(metadata["analysis_date"])}</span>'
        f'<a href="{home_href}">返回报告目录</a>'
        "</div></div></div>"
    )
    if not re.search(r"<body(?:\s[^>]*)?>", cleaned, re.IGNORECASE):
        raise PublishError("Report HTML has no body tag")
    cleaned = re.sub(r"(<body(?:\s[^>]*)?>)", r"\1\n" + shell, cleaned, count=1, flags=re.IGNORECASE)
    if not re.search(r"</body>", cleaned, re.IGNORECASE):
        raise PublishError("Report HTML has no closing body tag")
    bottom_return = (
        '<div class="publication-return">'
        f'<a href="{home_href}" aria-label="返回{html_lib.escape(config["site_name"])}报告目录">'
        '<span aria-hidden="true">←</span>返回报告目录'
        "</a></div>"
    )
    cleaned = re.sub(r"</body>", bottom_return + "\n</body>", cleaned, count=1, flags=re.IGNORECASE)
    trailing_newline = "\n" if cleaned.endswith("\n") else ""
    return "\n".join(line.rstrip() for line in cleaned.splitlines()) + trailing_newline


def _manifest_entry(metadata: dict[str, str], public_path: str, content_path: str) -> dict[str, str]:
    stock_slug = metadata["stock_code"].lower().replace(".", "-")
    report_id = f"{stock_slug}-{metadata['report_type']}-{metadata['analysis_date']}"
    return {
        "id": report_id,
        **metadata,
        "published_at": date.today().isoformat(),
        "public_path": public_path,
        "content_path": content_path,
    }


def publish_report(
    project_root: Path,
    source: Path,
    *,
    report_type: str | None = None,
    approve: bool = False,
    replace: bool = False,
    overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    project_root = project_root.resolve()
    source = source.resolve()
    if not source.is_file() or source.suffix.lower() not in {".html", ".htm"}:
        raise PublishError(f"Finished HTML report not found: {source}")
    resolved_type = infer_report_type(source, report_type)
    metadata = extract_report_metadata(source, resolved_type, overrides=overrides)

    stock_slug = metadata["stock_code"].lower().replace(".", "-")
    relative_dir = Path("reports") / stock_slug / resolved_type / metadata["analysis_date"]
    content_path = (relative_dir / "index.html").as_posix()
    public_path = content_path
    config = load_site_config(project_root / "site")
    prepared_html = prepare_report_html(
        source.read_text(encoding="utf-8"),
        config=config,
        metadata=metadata,
        public_path=public_path,
    )

    issues = inspect_public_text(
        prepared_html,
        known_secrets=load_known_local_secrets(project_root),
        require_report_contract=True,
    )
    if issues:
        raise PublishError(f"Report safety audit failed: {', '.join(issues)}")

    entry = _manifest_entry(metadata, public_path, content_path)
    if not approve:
        return entry

    site_root = project_root / "site"
    manifest_path = site_root / "content" / "reports.json"
    reports = load_report_manifest(site_root)
    existing_index = next((index for index, item in enumerate(reports) if item["id"] == entry["id"]), None)
    if existing_index is not None and not replace:
        raise PublishError(f"Report already approved: {entry['id']} (pass --replace to update)")

    destination = site_root / "content" / content_path
    previous_manifest = manifest_path.read_text(encoding="utf-8")
    previous_content = destination.read_bytes() if destination.exists() else None
    destination.parent.mkdir(parents=True, exist_ok=True)
    if existing_index is None:
        reports.append(entry)
    else:
        reports[existing_index] = entry

    try:
        destination.write_text(prepared_html, encoding="utf-8")
        manifest_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        build_site(project_root)
    except Exception:
        manifest_path.write_text(previous_manifest, encoding="utf-8")
        if previous_content is None:
            destination.unlink(missing_ok=True)
        else:
            destination.write_bytes(previous_content)
        raise
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Approve one finished HTML report for the static website")
    parser.add_argument("--report", required=True, help="Finished HTML report to approve")
    parser.add_argument("--type", choices=sorted(REPORT_TYPES), default=None, help="Report category (normally inferred)")
    parser.add_argument("--analysis-date", default="", help="Override analysis date (YYYY-MM-DD)")
    parser.add_argument("--title", default="", help="Override catalog title")
    parser.add_argument("--summary", default="", help="Override catalog summary")
    parser.add_argument("--verdict", default="", help="Override short verdict label")
    parser.add_argument("--industry", default="", help="Override industry label")
    parser.add_argument("--approve", action="store_true", help="Confirm this report may enter the public site")
    parser.add_argument("--replace", action="store_true", help="Replace an already approved report with the same id")
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent.parent
    overrides = {
        key: value
        for key, value in {
            "analysis_date": args.analysis_date,
            "title": args.title,
            "summary": args.summary,
            "verdict": args.verdict,
            "industry": args.industry,
        }.items()
        if value
    }
    try:
        entry = publish_report(
            project_root,
            Path(args.report),
            report_type=args.type,
            approve=args.approve,
            replace=args.replace,
            overrides=overrides,
        )
    except (PublishError, SiteBuildError) as exc:
        parser.error(str(exc))

    if args.approve:
        print(f"Approved and built: {entry['title']}")
        print(f"Public path: site/dist/{entry['public_path']}")
    else:
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        print("Preview only. Re-run with --approve to add this report to the public site.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
