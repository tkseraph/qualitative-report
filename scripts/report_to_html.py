#!/usr/bin/env python3
"""Convert {code_market}_qualitative_report.md to styled HTML dashboard.

Usage:
    python3 scripts/report_to_html.py \
        --input output/002078_太阳纸业/002078_SZ_qualitative_report.md \
        --output output/002078_太阳纸业/002078_SZ_qualitative_report.html

Optional:
    --template  Path to Jinja2 HTML template (default: shared/qualitative/templates/dashboard.html)
    --appendix  Path to framework_guide.md (default: shared/qualitative/references/framework_guide.md)
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

import markdown
from jinja2 import Environment, BaseLoader


# ---------------------------------------------------------------------------
# Markdown → HTML conversion
# ---------------------------------------------------------------------------

def md_to_html(md_text: str) -> str:
    """Convert markdown text to HTML with tables and fenced code support."""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )


def _is_reference_markdown_table(headers: list[str], rows: list[list[str]]) -> bool:
    table_tokens = " ".join(headers + [cell for row in rows for cell in row])
    reference_tokens = (
        "红旗项",
        "异常阈值",
        "重评动作",
        "触发项",
        "是否展开",
        "审计意见",
        "资金占用",
    )
    return any(token in table_tokens for token in reference_tokens)


def _is_large_markdown_table(table_text: str) -> bool:
    headers, rows = _parse_markdown_table(table_text)
    if _is_reference_markdown_table(headers, rows):
        return True
    return len(rows) >= 5


def _collapse_large_markdown_tables(md_text: str) -> str:
    def collapse(match: re.Match) -> str:
        table_text = match.group(1).strip()
        if not _is_large_markdown_table(table_text):
            return match.group(0)
        table_html = md_to_html(table_text)
        return (
            '<details class="dense-table-panel">\n'
            '<summary>完整数据表</summary>\n'
            '<div class="details-content">\n'
            f'{table_html}\n'
            '</div>\n'
            '</details>'
        )

    return re.sub(r"((?:\|.*\|\n?)+)", collapse, md_text)


def _summary_label_class(label: str) -> str:
    if any(token in label for token in ("风险", "反证", "重评", "触发")):
        return "risk"
    if any(token in label for token in ("证据", "验证", "依据")):
        return "evidence"
    return "thesis"


def _dimension_summary_cards_html(summary_md: str) -> str:
    cards = []
    item_pattern = r"^\s*(?:[-*]\s*)?(?:\*\*)?([^：:\n*]+)(?:\*\*)?[：:]\s*(.+?)\s*$"
    for match in re.finditer(item_pattern, summary_md, flags=re.MULTILINE):
        label = _strip_markdown_inline(match.group(1).strip())
        value = _strip_markdown_inline(match.group(2).strip())
        if label in {"本章结论", "最重要证据", "观察风险 / 重评触发", "观察风险", "重评触发", "核心证据"}:
            cards.append((label, value, _summary_label_class(label)))
    if not cards:
        return md_to_html(summary_md)
    card_html = "\n".join(
        f'<div class="dimension-summary-card summary-{css_class}"><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>'
        for label, value, css_class in cards
    )
    return f'<div class="dimension-summary-grid">\n{card_html}\n</div>'


def _promote_dimension_summary_cards(md_text: str) -> str:
    summary_labels = r"(?:本章结论|最重要证据|观察风险\s*/\s*重评触发|观察风险|重评触发|核心证据)"

    def promote(match: re.Match) -> str:
        title = match.group(1).strip()
        body = match.group("body").strip()
        return f'<div class="section-eyebrow">{html.escape(title)}</div>\n{_dimension_summary_cards_html(body)}'

    return re.sub(
        rf"^###\s+(本章小结|章节摘要|小结)\s*\n(?P<body>(?:(?:\s*[-*]\s*)?{summary_labels}[：:].+\n(?:\s*\n)?)+)",
        promote,
        md_text,
        flags=re.MULTILINE,
    )


def _cross_reassessment_card_class(label: str) -> str:
    if "支持" in label:
        return "support-card"
    if "削弱" in label:
        return "pressure-card"
    if "冲突" in label:
        return "conflict-card"
    if "触发" in label or "重评" in label:
        return "trigger-card"
    return "neutral-card"


def _cross_reassessment_cards_html(table_text: str) -> str:
    headers, rows = _parse_markdown_table(table_text)
    if len(headers) < 2 or not rows:
        return md_to_html(table_text)

    def cell(row: list[str], candidates: tuple[str, ...], fallback: int) -> str:
        for candidate in candidates:
            for index, header in enumerate(headers):
                if candidate in header and index < len(row):
                    return _strip_markdown_inline(row[index])
        return _strip_markdown_inline(row[fallback]) if fallback < len(row) else ""

    cards = []
    for row in rows:
        if not row:
            continue
        label = _strip_markdown_inline(row[0])
        evidence = cell(row, ("证据",), 1)
        explanation = cell(row, ("解释", "含义", "判断"), 2)
        action = cell(row, ("评级动作", "动作"), 3)
        css_class = _cross_reassessment_card_class(label)
        cards.append(
            '<div class="cross-reassessment-card {css_class}">'
            '<span>{label}</span>'
            '<strong>{evidence}</strong>'
            '{explanation_html}'
            '{action_html}'
            '</div>'.format(
                css_class=css_class,
                label=html.escape(label),
                evidence=html.escape(evidence),
                explanation_html=f'<p>{html.escape(explanation)}</p>' if explanation else '',
                action_html=f'<em>评级动作：{html.escape(action)}</em>' if action else '',
            )
        )
    return '<div class="cross-reassessment-grid">\n' + "\n".join(cards) + "\n</div>"


def _remove_embedded_chart_blocks(md_text: str, chart_titles: set[str]) -> str:
    if not chart_titles:
        return md_text

    def remove_if_chart(match: re.Match) -> str:
        title = match.group(1).strip()
        if title in chart_titles:
            return ""
        return match.group(0)

    return re.sub(
        r"^###\s+(.+?)\n(?P<body>.*?)(?=^##\s+|^###\s+|\Z)",
        remove_if_chart,
        md_text,
        flags=re.MULTILINE | re.DOTALL,
    )


def _promote_cross_reassessment_cards(md_text: str) -> str:
    def promote(match: re.Match) -> str:
        title = match.group(1).strip()
        body = match.group("body").strip()
        table_match = re.search(r"((?:\|.*\|\n?)+)", body)
        if not table_match:
            return match.group(0)
        before = body[:table_match.start()].strip()
        after = body[table_match.end():].strip()
        parts = [f'<h3 class="semantic-panel-heading cross-reassessment-panel">{html.escape(title)}</h3>']
        if before:
            parts.append(md_to_html(before))
        parts.append(_cross_reassessment_cards_html(table_match.group(1).strip()))
        if after:
            parts.append(md_to_html(after))
        return "\n".join(parts)

    return re.sub(
        r"^###\s+([^\n]*(?:评级复判|综合复判|复判表)[^\n]*)\n(?P<body>.*?)(?=^###\s+|\Z)",
        promote,
        md_text,
        flags=re.MULTILINE | re.DOTALL,
    )


def _sotp_card_value(headers: list[str], row: list[str], candidates: tuple[str, ...], fallback: int) -> str:
    for candidate in candidates:
        for index, header in enumerate(headers):
            if candidate in header and index < len(row):
                return _strip_markdown_inline(row[index])
    return _strip_markdown_inline(row[fallback]) if fallback < len(row) else ""


def _sotp_visual_panel_html(title: str, body: str, table_text: str) -> str:
    headers, rows = _parse_markdown_table(table_text)
    if len(headers) < 2 or not rows:
        return md_to_html(body)
    kind = "holding-network" if any(token in title for token in ("控股", "穿透", "网络", "层级")) else "subsidiary"
    intro = body[:body.find(table_text)].strip() if table_text in body else ""
    cards = []
    for row in rows:
        if not row:
            continue
        name = _sotp_card_value(headers, row, ("主体", "公司", "子公司"), 0)
        stake = _sotp_card_value(headers, row, ("持股", "口径", "层级"), 1)
        business = _sotp_card_value(headers, row, ("业务", "性质", "观察重点"), 2)
        meaning = _sotp_card_value(headers, row, ("价值", "含义", "重点"), 3)
        cards.append(
            '<div class="sotp-node-card">'
            f'<span>{html.escape(stake)}</span>'
            f'<strong>{html.escape(name)}</strong>'
            f'{f"<p>{html.escape(business)}</p>" if business else ""}'
            f'{f"<em>{html.escape(meaning)}</em>" if meaning else ""}'
            '</div>'
        )
    intro_html = md_to_html(intro) if intro else ""
    return (
        f'<div class="sotp-visual-panel" data-sotp-kind="{kind}">\n'
        f'<h3 class="semantic-panel-heading sotp-panel-heading">{html.escape(title)}</h3>\n'
        f'{intro_html}\n'
        '<div class="sotp-node-grid">\n'
        + "\n".join(cards)
        + "\n</div>\n"
        + md_to_html(table_text)
        + "\n</div>"
    )


def _promote_sotp_visual_panels(md_text: str) -> str:
    def promote(match: re.Match) -> str:
        title = match.group(1).strip()
        body = match.group("body").strip()
        table_match = re.search(r"((?:\|.*\|\n?)+)", body)
        if not table_match:
            return match.group(0)
        return _sotp_visual_panel_html(title, body, table_match.group(1).strip())

    return re.sub(
        r"^###\s+([^\n]*(?:子公司|控股|持股|投资收益|分部价值)[^\n]*)\n(?P<body>.*?)(?=^###\s+|\Z)",
        promote,
        md_text,
        flags=re.MULTILINE | re.DOTALL,
    )


def md_to_body_html(md_text: str, *, collapse_dense_tables: bool = False, promote_summary_cards: bool = False) -> str:
    if promote_summary_cards:
        md_text = _promote_dimension_summary_cards(md_text)
    if collapse_dense_tables:
        md_text = _collapse_large_markdown_tables(md_text)
    return md_to_html(md_text)


def _normalize_reader_phrasing(md_text: str) -> str:
    return re.sub(r"投资含义是\s*[：:]", "投资含义：", md_text)


def _decorate_status_terms(html_text: str) -> str:
    status_terms = (
        ("反证触发", "status-negative"),
        ("风险观察", "status-watch"),
        ("红旗", "status-negative"),
        ("下调", "status-negative"),
        ("正面", "status-positive"),
        ("中性", "status-neutral"),
        ("负面", "status-negative"),
    )
    pattern = re.compile("(" + "|".join(re.escape(term) for term, _ in status_terms) + ")")
    class_by_term = dict(status_terms)
    decorated_blocks = []
    for block in re.split(r"(<h[1-6][^>]*>.*?</h[1-6]>)", html_text, flags=re.DOTALL):
        if not block or re.match(r"<h[1-6]", block):
            decorated_blocks.append(block)
            continue
        parts = re.split(r"(<[^>]+>)", block)
        for index, part in enumerate(parts):
            if not part or part.startswith("<"):
                continue
            parts[index] = pattern.sub(
                lambda match: f'<span class="status-tag {class_by_term[match.group(1)]}">{match.group(1)}</span>',
                part,
            )
        decorated_blocks.append("".join(parts))
    return "".join(decorated_blocks)


def _decorate_semantic_panel_headings(html_text: str) -> str:
    semantic_classes = (
        (("利润桥", "可持续利润", "利润质量", "核心经营利润重算"), "profit-bridge-panel"),
        (("护城河六步审讯", "护城河审讯", "同业坐标", "竞争对标"), "moat-interrogation-panel"),
        (("治理红旗", "红旗排雷"), "governance-red-flag-panel"),
        (("MD&A 审讯", "MD&A审讯", "叙事审讯"), "mda-interrogation-panel"),
    )

    def decorate(match: re.Match) -> str:
        title = html.unescape(re.sub(r"<.*?>", "", match.group(1)))
        for keywords, class_name in semantic_classes:
            if any(keyword in title for keyword in keywords):
                return f'<h3 class="semantic-panel-heading {class_name}">{match.group(1)}</h3>'
        return match.group(0)

    return re.sub(r"<h3>(.*?)</h3>", decorate, html_text)


# ---------------------------------------------------------------------------
# Fallback inline CSS for --standalone mode when site CSS not found
# ---------------------------------------------------------------------------

_FALLBACK_CSS = """
:root{--bg:#fafaf7;--bg2:#f0efe9;--bg3:#e8e7e0;--text:#1c1c1a;--text2:#5c5c58;--text3:#8a8a84;--border:rgba(0,0,0,.08);--accent:#1a1a18;--green:#1a7a5a;--green-bg:#e6f4ee;--red:#c0392b;--red-bg:#fceaea;--amber:#a06c1a;--amber-bg:#faf0d8;--blue:#2563a0;--blue-bg:#e8f0fa;--purple:#6c5ce7;--purple-bg:#f0eefa;--cat-stock:#c0392b;--cat-essay:#2563a0;--cat-sector:#1a7a5a;--font:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC','Microsoft YaHei',system-ui,sans-serif;--mono:'JetBrains Mono','SF Mono','Fira Code',monospace;--max-width:820px;--padding-x:32px}
@media(prefers-color-scheme:dark){:root{--bg:#161614;--bg2:#1e1e1b;--bg3:#2a2a26;--text:#e8e7e0;--text2:#a0a098;--text3:#6a6a64;--border:rgba(255,255,255,.08);--accent:#e8e7e0;--green:#3dbb8a;--green-bg:#1a2e24;--red:#e86050;--red-bg:#2e1a1a;--amber:#d4a03a;--amber-bg:#2e2610;--blue:#5a9fd4;--blue-bg:#1a2430;--purple:#a29bfe;--purple-bg:#1e1a2e;--cat-stock:#e86050;--cat-essay:#5a9fd4;--cat-sector:#3dbb8a}}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.7;font-size:15px}
.container{max-width:var(--max-width);margin:0 auto;padding:0 var(--padding-x)}
.report-body{max-width:var(--max-width);margin:0 auto;padding:32px var(--padding-x) 64px;font-size:15px;line-height:1.7;color:var(--text)}
.report-body .header{border-bottom:2px solid var(--accent);padding-bottom:24px;margin-bottom:40px}.report-body .header .ticker{font-family:var(--mono);font-size:13px;color:var(--text3);letter-spacing:.5px;text-transform:uppercase}.report-body .header h1{font-size:28px;font-weight:600;margin:6px 0 4px;letter-spacing:-.5px}.report-body .header .date{font-size:13px;color:var(--text3)}
.report-body .verdict{display:flex;align-items:center;gap:12px;margin:24px 0;padding:16px 20px;background:var(--bg2);border-radius:8px;border-left:4px solid var(--green)}.verdict.v-green{border-left-color:var(--green)}.verdict.v-amber{border-left-color:var(--amber)}.verdict.v-red{border-left-color:var(--red)}.verdict-label{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:var(--text3);font-weight:500}.verdict-text{font-size:15px;font-weight:500}
.report-body h2{font-size:13px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--text3);margin:48px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border)}.report-body h2:first-of-type{margin-top:0}.report-body h3{font-size:15px;font-weight:600;color:var(--text);margin:24px 0 10px}.report-body h4{font-size:14px;font-weight:500;color:var(--text2);margin:16px 0 8px}
.report-body p{margin-bottom:14px;color:var(--text2)}.report-body p strong{color:var(--text);font-weight:500}.report-body ul,.report-body ol{margin:8px 0 14px 20px;color:var(--text2)}.report-body li{margin:4px 0}.report-body blockquote{border-left:3px solid var(--border);padding:8px 16px;margin:14px 0;color:var(--text3);font-style:italic;font-size:14px}
.report-body .grid{display:grid;gap:10px;margin:16px 0}.report-body .g4{grid-template-columns:1fr 1fr 1fr 1fr}@media(max-width:600px){.report-body .g4{grid-template-columns:1fr 1fr}}.report-body .metric{background:var(--bg2);border-radius:8px;padding:14px 16px}.report-body .metric .label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}.report-body .metric .value{font-family:var(--mono);font-size:20px;font-weight:500}.report-body .metric .sub{font-size:12px;color:var(--text3);margin-top:2px}
.report-body .metric.highlight{background:var(--green-bg);border:1px solid rgba(26,122,90,.15)}.report-body .metric.highlight .value{color:var(--green)}.report-body .metric.warn{background:var(--red-bg);border:1px solid rgba(192,57,43,.15)}.report-body .metric.warn .value{color:var(--red)}.report-body .metric.amber-hl{background:var(--amber-bg);border:1px solid rgba(160,108,26,.15)}.report-body .metric.amber-hl .value{color:var(--amber)}
.report-body .tag,.report-body .status-tag{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}.tag-green{background:var(--green-bg);color:var(--green)}.tag-red{background:var(--red-bg);color:var(--red)}.tag-amber{background:var(--amber-bg);color:var(--amber)}.status-positive{background:var(--green-bg);color:var(--green)}.status-neutral,.status-watch{background:var(--amber-bg);color:var(--amber)}.status-negative{background:var(--red-bg);color:var(--red)}
.badge-strong{background:var(--green-bg);color:var(--green)}.badge-fairly-strong{background:var(--green-bg);color:var(--green)}.badge-medium{background:var(--amber-bg);color:var(--amber)}.badge-weak{background:var(--red-bg);color:var(--red)}
.report-body table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}.report-body th{text-align:left;padding:8px 10px;font-weight:400;color:var(--text3);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;letter-spacing:.5px}.report-body th:not(:first-child){text-align:right}.report-body td{padding:8px 10px;border-bottom:1px solid var(--border)}.report-body td:not(:first-child){text-align:right;font-family:var(--mono);font-size:13px}.report-body tr:last-child td{border-bottom:none}
.report-body .callout{padding:16px 20px;background:var(--bg2);border-radius:8px;margin:20px 0;font-size:14px;color:var(--text2);line-height:1.7}
.report-body .sample-hero{padding:24px 0 8px;margin-bottom:28px;border-bottom:1px solid var(--border)}.report-body .sample-hero .header{border-bottom:0;margin-bottom:18px;padding-bottom:0}.report-body .article-meta-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0 8px}.report-body .article-meta-item{padding:10px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:8px}.report-body .article-meta-item span{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.8px;color:var(--text3)}.report-body .article-meta-item strong{display:block;margin-top:2px;font-size:12px;color:var(--text);font-weight:500}.report-body .research-flow-index{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:12px 0 4px;font-size:12px;color:var(--text3)}.report-body .research-flow-index span{letter-spacing:.5px}.report-body .research-flow-index strong{padding:3px 8px;background:var(--bg2);border:1px solid var(--border);border-radius:999px;color:var(--text2);font-weight:500}.report-body .hero-verdict{margin:18px 0}.report-body .hero-first-screen{background:var(--bg2);border:1px solid var(--border)}.report-body .section-eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:var(--text3);margin-bottom:8px;font-weight:600}
.report-body .hero-rating-stack{margin:18px 0;padding:18px 20px;background:var(--bg2);border:1px solid var(--border);border-radius:10px}.report-body .hero-rating-primary{font-size:28px;line-height:1.2;font-weight:600;color:var(--text);margin-bottom:6px}.report-body .hero-rating-stack p{margin:0;color:var(--text2)}.report-body .hero-thesis-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:16px 0 8px}.report-body .hero-thesis-card{padding:14px 16px;background:var(--bg2);border:1px solid var(--border);border-radius:10px}.report-body .hero-thesis-card span{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--text3);margin-bottom:5px}.report-body .hero-thesis-card strong{display:block;color:var(--text);font-size:14px;font-weight:600;line-height:1.5}.report-body .hero-moat-source{border-left:4px solid var(--green)}.report-body .hero-risk-card,.report-body .hero-refutation-card{border-left:4px solid var(--red)}.report-body .hero-company-essence{border-left:4px solid var(--blue)}@media(max-width:600px){.report-body .hero-thesis-grid{grid-template-columns:1fr}}.report-body .snapshot-grid{margin:12px 0}.report-body .snapshot-grid .metric{border:1px solid var(--border)}.report-body .executive-summary-card{background:var(--blue-bg);border:1px solid rgba(37,99,160,.12);color:var(--text2)}.report-body .risk-panel{background:var(--amber-bg);border:1px solid rgba(160,108,26,.14)}.report-body .research-article-section{margin:40px 0}.report-body .section-divider{height:1px;background:var(--border);margin:34px 0}.report-body .adaptive-research-panel{background:var(--green-bg);border:1px solid rgba(26,122,90,.14)}.report-body .cross-validation-panel{background:var(--amber-bg);border:1px solid rgba(160,108,26,.14)}.report-body .evidence-modules-panel{background:var(--blue-bg);border:1px solid rgba(37,99,160,.14)}.report-body .observation-panel{background:var(--bg2);border:1px solid var(--border)}.report-body .report-limitations-panel{background:var(--red-bg);border:1px solid rgba(192,57,43,.14)}.report-body .first-screen-thesis-card{border-left-width:4px}.report-body .semantic-panel-heading{padding:8px 10px;border-left:4px solid var(--border);background:var(--bg2);border-radius:8px}.report-body .profit-bridge-panel{border-left-color:var(--blue)}.report-body .moat-interrogation-panel{border-left-color:var(--green)}.report-body .governance-red-flag-panel{border-left-color:var(--red)}.report-body .mda-interrogation-panel{border-left-color:var(--amber)}.report-body .dimension-card{margin:34px 0;padding:0;background:transparent;border:0;border-radius:0}.report-body .dimension-card h2{margin-top:0}.report-body .dimension-content>p:first-child{font-size:15px;color:var(--text)}
.report-body .first-screen-card table,.report-body .future-observations table{margin:0}.report-body .first-screen-card td:not(:first-child),.report-body .future-observations td:not(:first-child){text-align:left;font-family:inherit}.report-body .core-contradiction{border-left:4px solid var(--amber)}.report-body .cross-reassessment-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:16px 0}.report-body .cross-reassessment-card{padding:14px 16px;background:var(--bg);border:1px solid var(--border);border-left:4px solid var(--border);border-radius:10px}.report-body .cross-reassessment-card span{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--text3);margin-bottom:5px}.report-body .cross-reassessment-card strong{display:block;color:var(--text);font-size:14px;line-height:1.5}.report-body .cross-reassessment-card p{margin:6px 0 0;font-size:13px}.report-body .cross-reassessment-card em{display:block;margin-top:8px;font-style:normal;font-size:12px;color:var(--text3)}.report-body .support-card{border-left-color:var(--green)}.report-body .pressure-card,.report-body .trigger-card{border-left-color:var(--red)}.report-body .conflict-card{border-left-color:var(--amber)}.report-body .cross-reassessment-panel{border-left-color:var(--purple)}@media(max-width:600px){.report-body .cross-reassessment-grid{grid-template-columns:1fr}}
	.report-body .trend-chart-section{margin:40px 0}.report-body .trend-chart-grid{display:grid;grid-template-columns:1fr;gap:16px}.report-body .trend-chart-card{background:var(--blue-bg);border:1px solid rgba(37,99,160,.14);border-radius:8px;padding:18px 20px}.report-body .trend-chart-title{font-size:15px;font-weight:600;color:var(--text);margin-bottom:8px}.report-body .trend-chart-readout{font-size:13px;color:var(--text2);margin-bottom:12px}.report-body .chart-container{height:220px;margin:12px 0;padding:12px;background:var(--bg);border:1px solid var(--border);border-radius:8px}.report-body .chart-container[data-chart-visual="mixed"]{border-left:4px solid var(--blue);background:linear-gradient(180deg,var(--bg),var(--blue-bg))}.report-body .chart-container[data-chart-visual="line"]{border-left:4px solid var(--green);background:linear-gradient(180deg,var(--bg),var(--green-bg))}.report-body .chart-container[data-chart-visual="bar"]{border-left:4px solid var(--amber);background:linear-gradient(180deg,var(--bg),var(--amber-bg))}.report-body .chart-container canvas{display:block;width:100%;height:100%}.report-body .chart-caption{font-size:12px;color:var(--text3);margin:6px 0 12px}.report-body .trend-chart-card table{margin:0;font-size:12px}.report-body .sotp-visual-panel{margin:18px 0;padding:18px 20px;background:var(--purple-bg);border:1px solid rgba(108,92,231,.14);border-radius:10px}.report-body .sotp-panel-heading{border-left-color:var(--purple)}.report-body .sotp-node-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0}.report-body .sotp-node-card{padding:14px 16px;background:var(--bg);border:1px solid var(--border);border-left:4px solid var(--purple);border-radius:10px}.report-body .sotp-node-card span{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.8px;color:var(--text3);margin-bottom:5px}.report-body .sotp-node-card strong{display:block;color:var(--text);font-size:14px}.report-body .sotp-node-card p{margin:6px 0 0;font-size:13px}.report-body .sotp-node-card em{display:block;margin-top:6px;font-style:normal;font-size:12px;color:var(--text3)}@media(max-width:700px){.report-body .sotp-node-grid{grid-template-columns:1fr}}
.report-body details{margin:16px 0}.report-body .appendix-panel{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:0 16px}.report-body summary{cursor:pointer;font-size:13px;font-weight:500;text-transform:uppercase;letter-spacing:1px;color:var(--text3);padding:10px 0;border-bottom:1px solid var(--border);user-select:none}.report-body details .details-content{padding:16px 0;font-size:14px;color:var(--text2)}
.report-body .footer{margin-top:56px;padding-top:20px;border-top:1px solid var(--border);font-size:12px;color:var(--text3);line-height:1.8}
a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
@media print{.report-body{padding:24px;font-size:12px;max-width:100%}}
"""


# Report parser – splits MD into logical sections
# ---------------------------------------------------------------------------

_RATING_MAP = {
    "强": ("rating-strong", "badge-strong"),
    "较强": ("rating-fairly-strong", "badge-fairly-strong"),
    "中": ("rating-medium", "badge-medium"),
    "中等": ("rating-medium", "badge-medium"),
    "弱": ("rating-weak", "badge-weak"),
    "高可持续": ("rating-strong", "badge-strong"),
    "中等可持续": ("rating-medium", "badge-medium"),
    "低可持续": ("rating-weak", "badge-weak"),
    "优秀": ("rating-strong", "badge-strong"),
    "合格": ("rating-fairly-strong", "badge-fairly-strong"),
    "损害价值": ("rating-weak", "badge-weak"),
    "观察期": ("rating-medium", "badge-medium"),
    "风险观察": ("rating-medium", "badge-medium"),
    "反证触发": ("rating-weak", "badge-weak"),
    "capital-light": ("rating-strong", "badge-strong"),
    "capital-hungry": ("rating-medium", "badge-medium"),
    "存在": ("rating-strong", "badge-strong"),
    "可能存在": ("rating-medium", "badge-medium"),
    "不存在": ("rating-weak", "badge-weak"),
    "正面": ("rating-strong", "badge-strong"),
    "中性": ("rating-medium", "badge-medium"),
    "负面": ("rating-weak", "badge-weak"),
    "低": ("rating-strong", "badge-strong"),
    "高": ("rating-weak", "badge-weak"),
}


def _rating_css(value: str) -> tuple[str, str]:
    """Return (kpi_card_class, badge_class) for a rating value."""
    for key, classes in _RATING_MAP.items():
        if key in value:
            return classes
    return ("rating-neutral", "")


def _extract_dimension_badge(body: str) -> str:
    badge_patterns = (
        r"(?:本章评级|维度评级|综合评价|竞争优势评价|治理评价|管理层评价|MD&A\s*可信度|资本消耗强度|周期状态|当前状态|风险状态|状态词)[：:]\s*\*?\*?([^。；;，,\n\*]+)",
    )
    allowed_badges = (
        "正面",
        "中性",
        "负面",
        "风险观察",
        "反证触发",
        "强",
        "较强",
        "中",
        "中等",
        "弱",
        "优秀",
        "合格",
        "损害价值",
    )
    for pattern in badge_patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE)
        if not match:
            continue
        raw_badge = _strip_markdown_inline(match.group(1)).strip()
        for badge in allowed_badges:
            if raw_badge == badge or raw_badge.startswith(badge):
                return badge
    return ""


def _find_structured_param(md_text: str, name: str) -> str:
    table_pattern = rf"\|\s*{re.escape(name)}\s*\|\s*(.+?)\s*\|"
    table_match = re.search(table_pattern, md_text)
    if table_match:
        return table_match.group(1).strip()
    yaml_pattern = rf"^\s*{re.escape(name)}\s*:\s*(.+?)\s*$"
    yaml_match = re.search(yaml_pattern, md_text, flags=re.MULTILINE)
    if yaml_match:
        return yaml_match.group(1).strip().strip('"\'')
    return ""


def _extract_first_screen_thesis(md_text: str) -> dict:
    section_match = re.search(
        r"^##\s+(?:Business Quality Verdict.*?|商业质量总体评级.*?)\n(?P<body>.*?)(?=^##\s+|\Z)",
        md_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not section_match:
        return {}
    table_match = re.search(r"((?:\|.*\|\n)+)", section_match.group("body"))
    if not table_match:
        return {}
    _headers, rows = _parse_markdown_table(table_match.group(1))
    values = {
        row[0].strip(): _strip_markdown_inline(row[1].strip())
        for row in rows
        if len(row) >= 2
    }
    return {
        "company_essence": values.get("公司本质", ""),
        "business_quality": values.get("商业质量", values.get("商业质量评级", "")),
        "moat_source": values.get("护城河来源", values.get("核心优势", "")),
        "max_risk": values.get("最大风险", ""),
        "refutation": values.get("反证条件", ""),
        "cycle_position": values.get("周期位置", ""),
    }


def _reader_value(name: str, value: str) -> str:
    normalized = value.strip().strip('"\'').lower()
    value_maps = {
        "moat_existence": {
            "true": "存在",
            "yes": "存在",
            "1": "存在",
            "false": "不存在",
            "no": "不存在",
            "0": "不存在",
        },
        "capital_intensity": {
            "capital-light": "轻资产",
            "asset-light": "轻资产",
            "light": "轻资产",
            "capital-hungry": "重资产",
            "asset-heavy": "重资产",
            "heavy": "重资产",
        },
        "cyclicality": {
            "weak-cycle": "弱周期",
            "low-cycle": "弱周期",
            "strong-cycle": "强周期",
            "high-cycle": "强周期",
        },
    }
    return value_maps.get(name, {}).get(normalized, value)


def _strip_markdown_inline(value: str) -> str:
    return re.sub(r"\*\*(.*?)\*\*", r"\1", value).strip()


def _parse_markdown_table(table_text: str) -> tuple[list[str], list[list[str]]]:
    rows = []
    for line in table_text.strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or re.fullmatch(r"[|:\-\s]+", stripped):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    if not rows:
        return [], []
    return rows[0], rows[1:]


_EXPLANATORY_CHART_COLUMNS = (
    "投资含义",
    "含义",
    "结论",
    "质量判断",
    "质量评价",
    "判断",
    "评价",
    "读法",
    "解释",
    "说明",
    "证据路径",
    "金额 / 证据",
    "金额/证据",
    "当前证据",
    "证据",
    "计算口径",
    "计算依据",
    "口径",
    "依据",
    "来源",
    "反证重点",
    "缺口处理",
    "重评动作",
    "动作",
    "沉默信息",
    "管理层理由",
    "理由",
    "后续结果",
    "实际结果",
    "实际兑现",
    "风险措辞变化",
    "下一年复核指标",
    "复核",
    "是否展开",
)


def _is_explanatory_chart_column(header: str) -> bool:
    return any(token in header for token in _EXPLANATORY_CHART_COLUMNS)


def _is_ratio_header(header: str) -> bool:
    normalized = header.replace("／", "/").replace("_", "/")
    return any(token in normalized for token in ("Capex/D&A", "Capex/DnA", "OCF/净利润", "OCF/NI"))


def _series_unit(header: str, sample_values: list[str]) -> str:
    if _is_ratio_header(header) or "倍" in header:
        return "x"
    if header.endswith("_pct") or any(token in header for token in ("率", "占比", "同比", "ROE", "ROA", "ROIC", "margin", "Margin")):
        return "%"
    if any(token in header for token in ("吨价", "吨成本", "吨毛利")):
        return "元/吨"
    if any("%" in value for value in sample_values):
        return "%"
    if any(token in header for token in ("收入", "利润", "金额", "FCF", "OCF", "Capex", "现金流", "市值")):
        return "亿元"
    return ""


def _series_role(header: str, chart_type: str, unit: str) -> str:
    if chart_type in {"bar-line-table", "bar-line-trend", "bar-table"}:
        if chart_type == "bar-table":
            return "bar" if unit not in {"%", "x"} else "line"
        if unit in {"%", "x"} or header.endswith("_pct") or any(token in header for token in ("率", "占比", "同比")):
            return "line"
        return "bar"
    return "line"


def _numeric_value(raw: str) -> float | None:
    number_match = re.search(r"-?\d+(?:\.\d+)?", raw.replace(",", ""))
    return float(number_match.group(0)) if number_match else None


def _is_year_header(value: str) -> bool:
    return bool(re.fullmatch(r"20\d{2}(?:年)?", value.strip()))


def _is_explicit_numbered_chart_title(title: str) -> bool:
    return bool(re.match(r"图表[一二三四五六七八九十]+[：:]", title))


def _chart_kind(chart_type: str) -> str:
    if chart_type in {"bar-line-table", "bar-line-trend"}:
        return "bar-line"
    if chart_type == "bar-table":
        return "bar"
    return "line"


def _chart_visual_grammar(chart_type: str) -> str:
    if chart_type in {"bar-line-table", "bar-line-trend"}:
        return "mixed"
    if chart_type == "bar-table":
        return "bar"
    return "line"


def _windowed_labels_and_rows(headers: list[str], rows: list[list[str]], chart_type: str) -> tuple[list[str], list[list[str]], str]:
    if headers and headers[0] in {"年份", "年度"} and len(rows) > 5:
        return headers, rows[-5:], "5y"
    return headers, rows, "all"


def _chart_series_payload(table_text: str, chart_type: str = "multi-series-trend") -> dict:
    headers, rows = _parse_markdown_table(table_text)
    if len(headers) < 2 or not rows:
        return {"labels": [], "datasets": [], "window": "all"}

    if headers[0] not in {"年份", "年度"} and sum(1 for header in headers[1:] if _is_year_header(header)) >= 2:
        year_columns = headers[1:]
        window = "5y" if len(year_columns) > 5 else "all"
        labels = year_columns[-5:]
        datasets = []
        for row in rows:
            if len(row) < 2:
                continue
            label = row[0]
            raw_values = row[1:][-5:]
            values = [_numeric_value(raw) for raw in raw_values]
            if any(value is not None for value in values):
                unit = _series_unit(label, raw_values)
                datasets.append({
                    "label": label,
                    "values": values,
                    "unit": unit,
                    "role": _series_role(label, chart_type, unit),
                })
        return {"labels": labels, "datasets": datasets, "window": window}

    headers, rows, window = _windowed_labels_and_rows(headers, rows, chart_type)
    labels = [row[0] for row in rows if row]
    datasets = []
    for column_index, header in enumerate(headers[1:], start=1):
        if _is_explanatory_chart_column(header):
            continue
        values = []
        raw_values = []
        for row in rows:
            raw = row[column_index] if column_index < len(row) else ""
            raw_values.append(raw)
            values.append(_numeric_value(raw))
        if any(value is not None for value in values):
            unit = _series_unit(header, raw_values)
            datasets.append({
                "label": header,
                "values": values,
                "unit": unit,
                "role": _series_role(header, chart_type, unit),
            })
    return {"labels": labels, "datasets": datasets, "window": window}


def _chart_series_json(table_text: str, chart_type: str = "multi-series-trend") -> str:
    payload = _chart_series_payload(table_text, chart_type)
    return html.escape(json.dumps(payload, ensure_ascii=False), quote=True)


def _reader_chart_title(title: str) -> str:
    return re.sub(r"^读图结论[：:]\s*", "", title).strip()


def _chart_canvas_html(title: str, readout: str, table_text: str, chart_type: str = "multi-series-trend") -> str:
    display_title = _reader_chart_title(title)
    caption = f"{display_title} — {readout}" if readout else display_title
    payload = _chart_series_payload(table_text, chart_type)
    return (
        f'<div class="chart-container" data-chart-type="{chart_type}" data-chart-kind="{_chart_kind(chart_type)}" data-chart-visual="{_chart_visual_grammar(chart_type)}" data-chart-window="{payload.get("window", "all")}" data-chart-title="{html.escape(display_title, quote=True)}" '
        f'data-chart-series="{html.escape(json.dumps(payload, ensure_ascii=False), quote=True)}">'
        f'<canvas aria-label="{html.escape(caption, quote=True)}"></canvas>'
        f'</div>'
        f'<p class="chart-caption">{html.escape(caption)}</p>'
    )


def _readout_from_body(body: str) -> str:
    readout_match = re.search(r"读图结论[：:]\s*(.+)", body)
    return readout_match.group(1).strip() if readout_match else ""


def _has_mixed_explicit_units_table(headers: list[str], rows: list[list[str]]) -> bool:
    if "单位" not in headers or len(headers) < 3:
        return False
    unit_index = headers.index("单位")
    value_headers = {"数值", "当前值", "当前值 / 本地证据", "值"}
    if not any(header in value_headers for header in headers[1:]):
        return False
    units = {
        row[unit_index].strip()
        for row in rows
        if unit_index < len(row) and row[unit_index].strip()
    }
    return len(units) > 1


def _is_clean_numeric_cell(raw: str) -> bool:
    stripped = raw.strip()
    if not stripped:
        return False
    if re.match(r"20\d{2}\s*年", stripped):
        return False
    return bool(re.fullmatch(r"-?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|亿元|百万元|万元|元/吨|元/kg|元|倍|x|X)?", stripped))


def _numeric_table_columns(headers: list[str], rows: list[list[str]]) -> list[int]:
    columns = []
    for column_index, header in enumerate(headers[1:], start=1):
        if _is_explanatory_chart_column(header):
            continue
        values = [row[column_index] if column_index < len(row) else "" for row in rows]
        clean_count = sum(1 for value in values if _is_clean_numeric_cell(value))
        numeric_count = sum(1 for value in values if _numeric_value(value) is not None)
        if clean_count and clean_count == numeric_count:
            columns.append(column_index)
    return columns


def _implicit_unit_category(row_label: str, raw_value: str) -> str:
    text = f"{row_label} {raw_value}"
    if _is_ratio_header(row_label) or any(token in text for token in ("/", "倍")):
        return "ratio"
    if "%" in text or any(token in row_label for token in ("率", "占比", "同比", "ROE", "ROA", "ROIC")):
        return "percent"
    if any(token in text for token in ("亿元", "百万元", "万元", "元", "现金流", "收入", "利润", "Capex", "D&A", "FCF", "OCF")):
        return "money"
    return "number"


def _has_mixed_implicit_units_single_value_table(headers: list[str], rows: list[list[str]]) -> bool:
    numeric_columns = _numeric_table_columns(headers, rows)
    if len(numeric_columns) != 1:
        return False
    value_header = headers[numeric_columns[0]]
    if not any(token in value_header for token in ("值", "当前", "数值")):
        return False
    categories = {
        _implicit_unit_category(row[0], row[numeric_columns[0]] if numeric_columns[0] < len(row) else "")
        for row in rows
        if row and numeric_columns[0] < len(row) and _numeric_value(row[numeric_columns[0]]) is not None
    }
    return len(categories) > 1


def _has_ambiguous_year_prefixed_numeric_cells(headers: list[str], rows: list[list[str]]) -> bool:
    for column_index, header in enumerate(headers[1:], start=1):
        if _is_explanatory_chart_column(header):
            continue
        for row in rows:
            raw = row[column_index] if column_index < len(row) else ""
            if _numeric_value(raw) is not None and re.search(r"20\d{2}\s*年[^|\n]*\d", raw):
                return True
    return False


def _is_chartable_table(table_text: str, title: str, chart_type: str) -> bool:
    headers, rows = _parse_markdown_table(table_text)
    if len(headers) < 2:
        return False
    numeric_columns = _numeric_table_columns(headers, rows)
    if _has_mixed_explicit_units_table(headers, rows):
        return False
    if _has_mixed_implicit_units_single_value_table(headers, rows):
        return False
    if _has_ambiguous_year_prefixed_numeric_cells(headers, rows):
        return False
    if _is_explicit_numbered_chart_title(title):
        return bool(numeric_columns)
    if sum(1 for header in headers[1:] if _is_year_header(header)) >= 2:
        return True
    if headers[0] in {"年份", "年度"}:
        return True
    if chart_type in {"bar-line-table", "bar-line-trend", "bar-table"} and any(keyword in title for keyword in ("业务", "收入质量", "吨经济", "单位经济", "区域毛利", "区域结构", "利润桥", "资本配置", "同业坐标", "同业对比", "竞争对标", "现金", "利润", "降本")):
        return bool(numeric_columns)
    return False


def _chart_type_from_metadata(body: str) -> str | None:
    match = re.search(r"^chart_ready:\s*true\s*;(?P<meta>.*)$", body, flags=re.MULTILINE)
    if not match:
        return None
    chart_type_match = re.search(r"chart_type:\s*(line|bar|mixed)\b", match.group("meta"))
    if not chart_type_match:
        return None
    chart_type = chart_type_match.group(1)
    if chart_type == "mixed":
        return "bar-line-table"
    if chart_type == "bar":
        return "bar-table"
    return "multi-series-trend"


def _chart_type_for_title(title: str, default: str = "multi-series-trend") -> str:
    if any(keyword in title for keyword in ("资本配置", "配置流向", "流向")):
        return "bar-table"
    if any(keyword in title for keyword in ("收入利润", "ROE因果链", "因果链", "同业坐标", "同业对比", "竞争对标", "现金", "利润", "降本")):
        return "bar-line-trend"
    return default


def _is_readout_chart_candidate(title: str, body: str) -> bool:
    if "读图结论" not in body or "|" not in body:
        return False
    return any(keyword in title + body for keyword in ("收入", "利润", "毛利", "费用", "现金", "OCF", "FCF", "Capex", "ROE", "同业", "区域", "业务", "资本"))


def _core_chart_target(title: str) -> str:
    strong_semantic_targets = (
        (("同业", "竞争对标", "护城河", "毛利率领先", "研发效率", "客户认证", "渠道控制", "转换成本"), "dimension_2"),
        (("外部", "周期", "需求", "价格", "宏观", "行业景气"), "dimension_3"),
        (("管理层", "MD&A", "叙事", "风险措辞", "兑现", "沉默信息"), "dimension_5"),
        (("治理", "资本配置", "分红", "回购", "并购", "红旗"), "dimension_4"),
        (("SOTP", "子公司", "投资收益", "控股", "分部价值"), "dimension_6"),
    )
    for keywords, target in strong_semantic_targets:
        if any(keyword in title for keyword in keywords):
            return target

    numbered_targets = (
        (("图表一",), "executive_summary"),
        (("图表二", "图表三", "图表四"), "dimension_1"),
        (("图表五",), "dimension_3"),
        (("图表六",), "dimension_2"),
    )
    for keywords, target in numbered_targets:
        if any(keyword in title for keyword in keywords):
            return target

    dimension_one_keywords = ("产品结构", "业务", "收入", "利润", "现金", "资本开支", "Capex", "FCF", "应收", "存货", "资本消耗")
    if any(keyword in title for keyword in dimension_one_keywords):
        return "dimension_1"
    if "ROE" in title:
        return "dimension_3"
    return "trend"


def _semantic_chart_title_class(title: str) -> str:
    semantic_classes = (
        (("利润桥", "可持续利润", "利润质量", "核心经营利润重算"), "semantic-panel-heading profit-bridge-panel"),
        (("护城河六步审讯", "护城河审讯", "同业坐标", "竞争对标"), "semantic-panel-heading moat-interrogation-panel"),
        (("治理红旗", "红旗排雷"), "semantic-panel-heading governance-red-flag-panel"),
        (("MD&A 审讯", "MD&A审讯", "叙事审讯"), "semantic-panel-heading mda-interrogation-panel"),
    )
    for keywords, class_name in semantic_classes:
        if any(keyword in title for keyword in keywords):
            return class_name
    return ""


def _chart_card(title: str, body: str, chart_type: str = "multi-series-trend", target_override: str | None = None) -> dict | None:
    table_match = re.search(r"((?:\|.*\|\n?)+)", body)
    if not table_match:
        return None
    table_text = table_match.group(1).strip()
    chart_type = _chart_type_from_metadata(body) or _chart_type_for_title(title, chart_type)
    if not _is_chartable_table(table_text, title, chart_type):
        return None
    payload = _chart_series_payload(table_text, chart_type)
    datasets = payload.get("datasets", [])
    if not datasets:
        return None
    if chart_type in {"bar-line-table", "bar-line-trend"} and len(datasets) > 5:
        return None
    if chart_type == "bar-table" and len(datasets) > 3:
        return None
    readout = _readout_from_body(body)
    return {
        "title": title,
        "readout": readout,
        "target": target_override or _core_chart_target(title),
        "title_class": _semantic_chart_title_class(title),
        "chart_html": _chart_canvas_html(title, readout, table_text, chart_type),
        "table_html": md_to_html(table_text),
    }


def _dimension_target_from_context(md_text: str, position: int) -> str | None:
    headings = list(re.finditer(r"^##\s+(.+?)(?:\n|$)", md_text[:position], flags=re.MULTILINE))
    if not headings:
        return None
    title = headings[-1].group(1).strip()
    if "维度" not in title and not re.match(r"D[1-6]\b", title, flags=re.IGNORECASE):
        return None
    dimension_index_match = re.search(r"(?:维度|D)\s*([1-6一二三四五六])", title, flags=re.IGNORECASE)
    if not dimension_index_match:
        return None
    dimension_number_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
    number = dimension_number_map.get(dimension_index_match.group(1), dimension_index_match.group(1))
    return f"dimension_{number}"


def _extract_trend_chart_cards(md_text: str) -> list[dict]:
    sections = [
        match.group(0)
        for match in re.finditer(
            r"^##\s+(?:关键趋势图表|近五年质量趋势|五年趋势|趋势证据).*?(?=^##\s+|\Z)",
            md_text,
            flags=re.MULTILINE | re.DOTALL,
        )
    ]
    if len(re.findall(r"^###\s+图表[一二三四五六七八九十]+[：:]", md_text, flags=re.MULTILINE)) < 5:
        sections.extend(
            f"### {match.group(1)}\n{match.group('body')}"
            for match in re.finditer(
                r"^###\s+((?:近五年质量趋势|五年趋势|趋势证据).+?|近五年质量趋势|五年趋势|趋势证据)\n(?P<body>.*?)(?=^##\s+|^###\s+|\Z)",
                md_text,
                flags=re.MULTILINE | re.DOTALL,
            )
        )

    cards: list[dict] = []
    for section in sections:
        for match in re.finditer(
            r"^###\s+(.+?)\n(?P<body>.*?)(?=^###\s+|\Z)",
            section,
            flags=re.MULTILINE | re.DOTALL,
        ):
            title = match.group(1).strip()
            body = match.group("body").strip()
            table_match = re.search(r"((?:\|.*\|\n?)+)", body)
            if not table_match:
                continue
            if not _is_explicit_numbered_chart_title(title) and "年份" not in table_match.group(1):
                continue
            card = _chart_card(title, body)
            if card:
                cards.append(card)
        if not cards:
            table_match = re.search(r"((?:\|.*\|\n?)+)", section)
            if table_match and "年份" in table_match.group(1):
                title = section.splitlines()[0].lstrip("# ").strip()
                table_text = table_match.group(1).strip()
                cards.append({
                    "title": title,
                    "readout": "",
                    "target": _core_chart_target(title),
                    "chart_html": _chart_canvas_html(title, "", table_text),
                    "table_html": md_to_html(table_text),
                })
    explicit_cards = [card for card in cards if _is_explicit_numbered_chart_title(card["title"])]
    if len(explicit_cards) >= 5:
        return explicit_cards

    chart_table_headings = (
        "业务拆分",
        "收入质量拆分",
        "业务板块",
        "吨经济模型",
        "单位经济模型",
        "区域毛利率",
        "区域结构",
        "利润桥",
        "利润质量",
        "资本消耗",
        "现金质量",
        "现金转化",
        "行业地图",
        "量化验证",
        "周期位置",
        "外部变量",
        "竞争对标",
        "同业坐标",
        "同业对比",
        "资本配置",
        "收入利润",
        "因果链",
        "配置流向",
    )
    for match in re.finditer(
        r"^###\s+(.+?)\n(?P<body>.*?)(?=^##\s+|^###\s+|\Z)",
        md_text,
        flags=re.MULTILINE | re.DOTALL,
    ):
        title = match.group(1).strip()
        body = match.group("body").strip()
        if not any(keyword in title for keyword in chart_table_headings) and not _is_readout_chart_candidate(title, body):
            continue
        card = _chart_card(title, body, "bar-line-table", target_override=_dimension_target_from_context(md_text, match.start()))
        if card and card["title"] not in {existing["title"] for existing in cards}:
            cards.append(card)
    explicit_cards = [card for card in cards if _is_explicit_numbered_chart_title(card["title"])]
    if len(explicit_cards) >= 5:
        return explicit_cards
    return cards


def parse_report(md_text: str) -> dict:
    """Parse the qualitative report MD into structured sections."""
    result = {
        "company_name": "",
        "stock_code": "",
        "generated_date": "",
        "executive_summary": "",
        "first_screen_card": "",
        "core_contradiction": "",
        "adaptive_research_plan": "",
        "cross_validation_research": "",
        "evidence_modules": "",
        "future_observations": "",
        "limitations_warnings": "",
        "trend_charts": [],
        "executive_charts": [],
        "dimensions": [],
        "conclusion": "",
        "parameters_table": "",
    }

    md_text = md_text.lstrip()
    chart_cards = _extract_trend_chart_cards(md_text)
    result["executive_charts"] = [card for card in chart_cards if card.get("target") == "executive_summary"]
    result["trend_charts"] = [card for card in chart_cards if card.get("target") == "trend"]
    dimension_chart_cards = {
        f"dimension_{index}": [card for card in chart_cards if card.get("target") == f"dimension_{index}"]
        for index in range(1, 7)
    }
    result["has_embedded_charts"] = bool(result["executive_charts"] or any(dimension_chart_cards.values()))

    # --- Extract title metadata ---
    # Format A: "# 定性分析 — CompanyName (Code)"
    title_match = re.search(r"#\s+定性分析.*?—\s*(.+?)\s*\((.+?)\)", md_text)
    if title_match:
        result["company_name"] = title_match.group(1)
        result["stock_code"] = title_match.group(2)
    else:
        # Format B: "# 美的集团（000333.SZ / 0300.HK）— 商业模式与护城河定性分析"
        title_match_b = re.search(
            r"#\s+(.+?)\s*[（(](.+?)[）)]\s*—", md_text
        )
        if title_match_b:
            result["company_name"] = title_match_b.group(1).strip()
            result["stock_code"] = title_match_b.group(2).strip()
        else:
            title_match_c = re.search(
                r"#\s+(.+?)\s*[（(](.+?)[）)]\s*(?:商业模式|定性分析|商业质量评估|质量评估)", md_text
            )
            if title_match_c:
                result["company_name"] = title_match_c.group(1).strip()
                result["stock_code"] = title_match_c.group(2).strip()

    # Date extraction: try multiple formats
    date_match = re.search(r"\*生成时间:\s*(.+?)\*", md_text)
    if date_match:
        result["generated_date"] = date_match.group(1)
    else:
        # Format B: "> 分析日期：2026-04-05" or footer "分析日期 2026-04-05"
        date_match_b = re.search(r"分析日期[：:\s]+(\d{4}-\d{2}-\d{2})", md_text)
        if date_match_b:
            result["generated_date"] = date_match_b.group(1)

    # --- Split by ## headers ---
    sections = re.split(r"(?=^## )", md_text, flags=re.MULTILINE)
    rendered_dimension_chart_targets: set[str] = set()

    for section in sections:
        header_match = re.match(r"## (.+?)(?:\n|$)", section)
        if not header_match:
            continue
        title = header_match.group(1).strip()
        body = section[header_match.end():]
        h3_conclusion_match = re.search(
            r"^###\s+[^\n]*(?:深度总结|核心投资逻辑|综合复判|最终复判)[^\n]*\n(?P<body>.*?)(?=^##\s+|^###\s+|\Z)",
            body,
            flags=re.MULTILINE | re.DOTALL,
        )
        if h3_conclusion_match and not result["conclusion"]:
            result["conclusion"] = md_to_html(h3_conclusion_match.group("body"))

        if "执行摘要" in title or "Executive Summary" in title:
            if result["executive_charts"]:
                body = _remove_embedded_chart_blocks(body, {chart["title"] for chart in result["executive_charts"]})
            result["executive_summary"] = md_to_html(body)
        elif "Business Quality Verdict" in title or "商业质量总体评级" in title:
            table_match = re.search(r"((?:\|.*\|\n)+)", body)
            if table_match and "项目" in table_match.group(1) and "结论" in table_match.group(1):
                result["first_screen_card"] = md_to_html(table_match.group(1))
        elif "核心矛盾" in title or "反证条件" in title:
            result["core_contradiction"] = md_to_html(body)
        elif "自适应研究计划" in title:
            result["adaptive_research_plan"] = md_to_html(body)
        elif "交叉验证与深度分析" in title or "交叉验证" in title:
            result["cross_validation_research"] = _decorate_status_terms(_promote_cross_reassessment_cards(body))
        elif "样板证据模块" in title or "证据模块" in title:
            result["evidence_modules"] = _decorate_semantic_panel_headings(md_to_html(body))
        elif "未来观察" in title or "观察变量" in title:
            result["future_observations"] = md_to_html(body)
        elif "报告局限" in title or "数据警示" in title:
            result["limitations_warnings"] = md_to_html(body)
        elif "总结与投资启示" in title or "深度总结" in title:
            result["conclusion"] = md_to_html(body)
        elif "结构化参数" in title:
            result["parameters_table"] = md_to_html(body)
        elif "维度" in title or re.match(r"D[1-6]\b", title, flags=re.IGNORECASE):
            # Extract badge from subsection summaries
            badge = _extract_dimension_badge(body)
            badge_class = ""
            if badge:
                _, badge_class = _rating_css(badge)

            dimension_index_match = re.search(r"(?:维度|D)\s*([1-6一二三四五六])", title, flags=re.IGNORECASE)
            dimension_number_map = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
            dimension_number = ""
            if dimension_index_match:
                dimension_number = dimension_number_map.get(dimension_index_match.group(1), dimension_index_match.group(1))

            chart_target = f"dimension_{dimension_number}"
            charts = dimension_chart_cards.get(chart_target, [])
            if charts:
                rendered_dimension_chart_targets.add(chart_target)
                body = _remove_embedded_chart_blocks(body, {chart["title"] for chart in charts})
            if dimension_number == "6":
                body = _promote_sotp_visual_panels(body)
            body_html = md_to_body_html(body, collapse_dense_tables=True, promote_summary_cards=True)
            body_html = _decorate_status_terms(_decorate_semantic_panel_headings(body_html))
            result["dimensions"].append({
                "title": title,
                "content": body_html,
                "badge": badge,
                "badge_class": badge_class,
                "charts": charts,
            })

    for target, cards in dimension_chart_cards.items():
        if target not in rendered_dimension_chart_targets:
            result["trend_charts"].extend(cards)

    return result


def extract_kpi_cards(md_text: str) -> list[dict]:
    """Extract KPI values from the structured parameters table."""
    cards = []

    def _find_param(name: str) -> str:
        return _reader_value(name, _find_structured_param(md_text, name))

    def _to_card_css(value: str) -> str:
        """Map rating text to card CSS class."""
        positive = ["强", "优秀", "存在", "高可持续", "正面", "capital-light"]
        negative = ["弱", "损害价值", "不存在", "低可持续", "负面"]
        neutral = ["中", "中等", "合格", "观察期", "中等可持续", "capital-hungry", "可能存在"]
        for p in positive:
            if p in value:
                return "highlight"
        for n in negative:
            if n in value:
                return "warn"
        for m in neutral:
            if m in value:
                return "amber-hl"
        return ""

    # ROE
    roe = _find_param("roe_5y_avg")
    if roe:
        try:
            roe_val = float(re.search(r"[\d.]+", roe).group())
            css = "highlight" if roe_val >= 15 else ("amber-hl" if roe_val >= 8 else "warn")
        except (ValueError, AttributeError):
            css = ""
        cards.append({"label": "5Y Avg ROE", "value": roe, "css_class": css, "sub": ""})

    # Moat rating
    moat = _find_param("moat_rating")
    if moat:
        cards.append({"label": "护城河评级", "value": moat, "css_class": _to_card_css(moat), "sub": ""})

    # Sustainability
    sust = _find_param("moat_sustainability")
    if sust:
        cards.append({"label": "可持续性", "value": sust, "css_class": _to_card_css(sust), "sub": ""})

    # Management
    mgmt = _find_param("management_rating")
    if mgmt:
        cards.append({"label": "管理层评价", "value": mgmt, "css_class": _to_card_css(mgmt), "sub": ""})

    # Cyclicality
    cyc = _find_param("cyclicality")
    if cyc:
        pos = _find_param("cycle_position")
        cards.append({"label": "周期性", "value": cyc, "css_class": "", "sub": pos if pos else ""})

    # Capital intensity
    cap = _find_param("capital_intensity")
    if cap:
        cards.append({"label": "资本强度", "value": cap, "css_class": _to_card_css(cap), "sub": ""})

    # Entry barrier
    barrier = _find_param("entry_barrier")
    if barrier:
        cards.append({"label": "进入壁垒", "value": barrier, "css_class": _to_card_css(barrier), "sub": ""})

    # Moat existence
    exist = _find_param("moat_existence")
    if exist:
        cards.append({"label": "优势存在性", "value": exist, "css_class": _to_card_css(exist), "sub": ""})

    return cards


def extract_data_pack_info(dp_text: str) -> dict:
    """Extract header-level info from data_pack_market.md."""
    info = {
        "current_price": "",
        "market_cap": "",
        "exchange": "",
        "industry": "",
    }

    price_m = re.search(r"当前价格[|\s]+(\d+\.?\d*)", dp_text)
    if price_m:
        info["current_price"] = price_m.group(1)

    mcap_m = re.search(r"总市值\s*\(万元\)\s*\|\s*([\d,.]+)", dp_text)
    if mcap_m:
        val = mcap_m.group(1).replace(",", "")
        try:
            v = float(val)
            info["market_cap"] = f"{v / 10000:.0f}亿"
        except ValueError:
            info["market_cap"] = mcap_m.group(1)

    exchange_m = re.search(r"交易所\s*\|\s*(\S+)", dp_text)
    if exchange_m:
        info["exchange"] = exchange_m.group(1)

    industry_m = re.search(r"行业\s*\|\s*(\S+)", dp_text)
    if industry_m:
        info["industry"] = industry_m.group(1)

    return info


def build_verdict(md_text: str) -> dict:
    """Build the verdict banner from the report's moat_rating and conclusion."""
    def _find_param(name: str) -> str:
        return _reader_value(name, _find_structured_param(md_text, name))

    moat = _find_param("moat_rating")
    sust = _find_param("moat_sustainability")

    # Extract one-line final conclusion if present
    verdict_text = ""
    final_m = re.search(
        r"(?:一句话最终结论|一句话结论)[：:]\s*\*?\*?(.+?)(?:\*?\*?\s*$|\n)",
        md_text, re.MULTILINE,
    )
    if final_m:
        verdict_text = final_m.group(1).strip().strip("*")
    else:
        # Fallback: build from params
        verdict_text = f"护城河评级 {moat}，可持续性 {sust}" if moat else ""

    # Determine color
    tag_map = {
        "强": ("tag-green", "v-green", "STRONG MOAT"),
        "较强": ("tag-green", "v-green", "FAIRLY STRONG"),
        "中": ("tag-amber", "v-amber", "MODERATE"),
        "弱": ("tag-red", "v-red", "WEAK"),
    }
    tag_class, verdict_class, tag_text = tag_map.get(
        moat, ("tag-amber", "v-amber", moat.upper() if moat else "N/A")
    )

    return {
        "verdict_class": verdict_class,
        "verdict_tag_class": tag_class,
        "verdict_tag": tag_text,
        "verdict_text": verdict_text,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_report_html(
    input_path: Path,
    output_path: Path,
    *,
    template_path: Path | None = None,
    appendix_path: Path | None = None,
    data_pack_path: Path | None = None,
    standalone: bool = False,
) -> None:
    """Render a qualitative markdown report to the HTML dashboard template."""
    project_root = Path(__file__).resolve().parent.parent
    template_path = template_path or project_root / "shared" / "qualitative" / "templates" / "dashboard.html"
    appendix_path = appendix_path or project_root / "shared" / "qualitative" / "references" / "framework_guide.md"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # --- Read inputs ---
    md_text = _normalize_reader_phrasing(input_path.read_text(encoding="utf-8"))
    template_text = template_path.read_text(encoding="utf-8")

    appendix_html = ""
    if appendix_path.exists():
        appendix_md = appendix_path.read_text(encoding="utf-8")
        appendix_html = md_to_html(appendix_md)

    # --- Parse report ---
    report = parse_report(md_text)
    kpi_cards = extract_kpi_cards(md_text)
    verdict = build_verdict(md_text)
    first_screen_thesis = _extract_first_screen_thesis(md_text)

    # Try to get data pack info
    dp_info = {"current_price": "", "market_cap": "", "exchange": "", "industry": ""}
    data_pack_path = data_pack_path or input_path.parent / "data_pack_market.md"
    if data_pack_path.exists():
        dp_text = data_pack_path.read_text(encoding="utf-8")
        dp_info = extract_data_pack_info(dp_text)

    # --- Load standalone CSS if requested ---
    standalone_css = ""
    if standalone:
        # Try to load style.css + report.css from terancejiang.com project
        site_root = Path.home() / "Projects" / "Teracnejiang.com"
        css_parts = []
        for css_file in ["assets/css/style.css", "assets/css/report.css"]:
            css_path = site_root / css_file
            if css_path.exists():
                css_parts.append(css_path.read_text(encoding="utf-8"))
        if css_parts:
            standalone_css = "\n".join(css_parts)
        else:
            # Fallback: minimal inline CSS for local viewing
            standalone_css = _FALLBACK_CSS

    # --- Generate slug ---
    slug = ""
    if report["stock_code"]:
        code = report["stock_code"].replace(".SH", "").replace(".SZ", "").replace(".HK", "").replace(".US", "")
        name = report["company_name"] or ""
        # Simple slug: company-code-qualitative
        slug = f"{name}-{code}-qualitative".lower().replace(" ", "-")

    # --- Render template ---
    env = Environment(loader=BaseLoader())
    template = env.from_string(template_text)
    html = template.render(
        company_name=report["company_name"],
        stock_code=report["stock_code"],
        generated_date=report["generated_date"],
        current_price=dp_info["current_price"],
        market_cap=dp_info["market_cap"],
        exchange=dp_info["exchange"],
        industry=dp_info["industry"],
        slug=slug,
        standalone_css=standalone_css,
        kpi_cards=kpi_cards,
        executive_summary=report["executive_summary"],
        first_screen_card=report["first_screen_card"],
        first_screen_thesis=first_screen_thesis,
        core_contradiction=report["core_contradiction"],
        adaptive_research_plan=report["adaptive_research_plan"],
        cross_validation_research=report["cross_validation_research"],
        evidence_modules=report["evidence_modules"],
        future_observations=report["future_observations"],
        limitations_warnings=report["limitations_warnings"],
        trend_charts=report["trend_charts"],
        executive_charts=report["executive_charts"],
        dimensions=report["dimensions"],
        has_trend_charts=bool(report["trend_charts"] or report.get("has_embedded_charts")),
        conclusion=report["conclusion"],
        parameters_table=report["parameters_table"],
        framework_guide=appendix_html,
        **verdict,
    )

    # --- Write output ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML report generated: {output_path}")
    print(f"  Sections: {len(report['dimensions'])} dimensions")
    print(f"  KPI cards: {len(kpi_cards)}")
    print(f"  Has executive summary: {bool(report['executive_summary'])}")
    print(f"  Has conclusion: {bool(report['conclusion'])}")
    print(f"  Has appendix: {bool(appendix_html)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Convert qualitative report MD to HTML dashboard")
    parser.add_argument("--input", required=True, help="Path to {code_market}_qualitative_report.md")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument(
        "--template",
        default=None,
        help="Jinja2 template path (default: auto-detect from project root)",
    )
    parser.add_argument(
        "--appendix",
        default=None,
        help="Path to framework_guide.md (default: auto-detect)",
    )
    parser.add_argument(
        "--data-pack",
        default=None,
        help="Path to data_pack_market.md for header stats extraction",
    )
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Embed CSS inline for local viewing (no external CSS dependencies)",
    )
    args = parser.parse_args()

    try:
        render_report_html(
            Path(args.input),
            Path(args.output),
            template_path=Path(args.template) if args.template else None,
            appendix_path=Path(args.appendix) if args.appendix else None,
            data_pack_path=Path(args.data_pack) if args.data_pack else None,
            standalone=args.standalone,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
