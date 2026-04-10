#!/usr/bin/env python3
"""Convert turtle markdown report to dedicated HTML page."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import markdown
from jinja2 import Environment, BaseLoader

_FALLBACK_CSS = """
:root{--bg:#fafaf7;--bg2:#f0efe9;--bg3:#e8e7e0;--text:#1c1c1a;--text2:#5c5c58;--text3:#8a8a84;--border:rgba(0,0,0,.08);--accent:#1a1a18;--green:#1a7a5a;--green-bg:#e6f4ee;--red:#c0392b;--red-bg:#fceaea;--amber:#a06c1a;--amber-bg:#faf0d8;--blue:#2563a0;--blue-bg:#e8f0fa;--max-width:920px;--padding-x:32px}
@media(prefers-color-scheme:dark){:root{--bg:#141414;--bg2:#1e1e1e;--bg3:#2a2a2a;--text:#e8e8e4;--text2:#a8a8a0;--text3:#6e6e68;--border:rgba(255,255,255,.08);--accent:#e8e8e4;--green:#4ade80;--green-bg:rgba(74,222,128,.1);--red:#f87171;--red-bg:rgba(248,113,113,.1);--amber:#fbbf24;--amber-bg:rgba(251,191,36,.1);--blue:#60a5fa;--blue-bg:rgba(96,165,250,.1)}}
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.7;font-size:15px}
.container{max-width:var(--max-width);margin:0 auto;padding:0 var(--padding-x)}.site-nav{display:flex;align-items:center;justify-content:space-between;padding:16px 0;border-bottom:1px solid var(--border)}.nav-logo{color:var(--text);text-decoration:none;font-weight:600;font-size:15px}.nav-links{display:flex;gap:20px}.nav-links a{color:var(--text3);text-decoration:none;font-size:14px}.nav-links a.active{color:var(--text)}
.report-body{max-width:var(--max-width);margin:0 auto;padding:32px var(--padding-x) 64px;font-size:15px;line-height:1.7;color:var(--text)}
.header{border-bottom:2px solid var(--accent);padding-bottom:24px;margin-bottom:32px}.ticker{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--text3);letter-spacing:.5px;text-transform:uppercase}.header h1{font-size:28px;font-weight:600;margin:6px 0 4px;letter-spacing:-.5px}.date{font-size:13px;color:var(--text3)}
.verdict{display:flex;align-items:center;gap:12px;margin:24px 0;padding:16px 20px;background:var(--bg2);border-radius:8px;border-left:4px solid var(--amber)}.v-green{border-left-color:var(--green)}.v-amber{border-left-color:var(--amber)}.v-red{border-left-color:var(--red)}.tag{display:inline-block;font-size:11px;padding:2px 8px;border-radius:4px;font-weight:500}.tag-green{background:var(--green-bg);color:var(--green)}.tag-red{background:var(--red-bg);color:var(--red)}.tag-amber{background:var(--amber-bg);color:var(--amber)}
.grid{display:grid;gap:10px;margin:16px 0}.g4{grid-template-columns:repeat(4,1fr)}@media(max-width:700px){.g4{grid-template-columns:repeat(2,1fr)}}.metric{background:var(--bg2);border-radius:8px;padding:14px 16px}.label{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}.value{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:500}.sub{font-size:12px;color:var(--text3);margin-top:2px}.metric.highlight{background:var(--green-bg)}.metric.warn{background:var(--red-bg)}.metric.amber-hl{background:var(--amber-bg)}
h2{font-size:13px;font-weight:500;text-transform:uppercase;letter-spacing:1.5px;color:var(--text3);margin:40px 0 16px;padding-bottom:8px;border-bottom:1px solid var(--border)}h3{font-size:15px;font-weight:600;color:var(--text);margin:24px 0 10px}p{margin-bottom:14px;color:var(--text2)}p strong{color:var(--text)}ul,ol{margin:8px 0 14px 20px;color:var(--text2)}li{margin:4px 0}.callout{padding:16px 20px;background:var(--bg2);border-radius:8px;margin:20px 0;font-size:14px;color:var(--text2);line-height:1.7}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:13px}th{text-align:left;padding:8px 10px;font-weight:400;color:var(--text3);border-bottom:1px solid var(--border);font-size:11px;text-transform:uppercase;letter-spacing:.5px}th:not(:first-child){text-align:right}td{padding:8px 10px;border-bottom:1px solid var(--border)}td:not(:first-child){text-align:right;font-family:'JetBrains Mono',monospace;font-size:13px}
.footer{margin-top:56px;padding-top:20px;border-top:1px solid var(--border);font-size:12px;color:var(--text3);line-height:1.8}
"""


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["tables", "fenced_code", "nl2br", "sane_lists"])


def extract_section(md_text: str, title: str) -> str:
    pattern = rf"(?ms)^##\s+{re.escape(title)}\n(.*?)(?=^##\s+|\Z)"
    m = re.search(pattern, md_text)
    return m.group(1).strip() if m else ""


def extract_header(md_text: str) -> dict:
    title = re.search(r"#\s+龟龟投资策略\s*·\s*分析报告：(.+?)（(.+?)）", md_text)
    date = re.search(r"分析日期\s*\|\s*(\d{4}-\d{2}-\d{2})", md_text)
    return {
        "company_name": title.group(1).strip() if title else "",
        "stock_code": title.group(2).strip() if title else "",
        "date": date.group(1) if date else "",
    }


def extract_simple(md_text: str, pattern: str) -> str:
    m = re.search(pattern, md_text)
    return m.group(1).strip() if m else ""


def build_summary(md_text: str) -> dict:
    return {
        "current_price": extract_simple(md_text, r"最新股价\s*\|\s*([^|\n]+)"),
        "verdict": extract_simple(md_text, r"\*\*仓位建议\*\*\s*\|\s*\*\*([^*]+)\*\*"),
        "gg": extract_simple(md_text, r"精算穿透回报率\s*\|\s*([^|\n]+)"),
        "ii": extract_simple(md_text, r"门槛值\s*\|\s*([^|\n]+)"),
        "margin": extract_simple(md_text, r"安全边际\s*\|\s*([^|\n]+)"),
        "trap": extract_simple(md_text, r"价值陷阱风险\s*\|\s*([^|\n]+)"),
        "credibility": extract_simple(md_text, r"外推可信度\s*\|\s*([^|\n]+)"),
    }


def verdict_style(text: str) -> tuple[str, str]:
    if any(k in text for k in ["标准仓位", "50%", "70%", "买入"]):
        return "v-green", "tag-green"
    if any(k in text for k in ["不建仓", "排除"]):
        return "v-red", "tag-red"
    return "v-amber", "tag-amber"


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert turtle markdown report to HTML page")
    parser.add_argument("--input", required=True, help="Path to turtle markdown report")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--template", default=None, help="Jinja2 template path")
    parser.add_argument("--standalone", action="store_true", help="Embed CSS inline")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    input_path = Path(args.input)
    output_path = Path(args.output)
    template_path = Path(args.template) if args.template else project_root / "strategies" / "turtle" / "references" / "turtle_report_dashboard.html"

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    if not template_path.exists():
        raise SystemExit(f"Template not found: {template_path}")

    md_text = input_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    header = extract_header(md_text)
    summary = build_summary(md_text)
    verdict_class, verdict_tag_class = verdict_style(summary["verdict"])

    meta_html = md_to_html(extract_section(md_text, "报告元信息"))
    exec_html = md_to_html(extract_section(md_text, "Executive Summary"))
    assumptions_html = md_to_html(extract_section(md_text, "关键假设"))
    trends_html = md_to_html(extract_section(md_text, "财务趋势速览"))
    quality_html = md_to_html(extract_section(md_text, "商业质量分析"))
    quant_html = md_to_html(extract_section(md_text, "穿透回报率分析"))
    valuation_html = md_to_html(extract_section(md_text, "估值与定价"))
    conclusion_html = md_to_html(extract_section(md_text, "综合结论"))
    thesis_html = md_to_html(extract_section(md_text, "投资论点卡（Thesis Card）"))

    key_cards = [
        {"label": "当前股价", "value": summary["current_price"], "css_class": "", "sub": ""},
        {"label": "精算回报率 GG", "value": summary["gg"], "css_class": "amber-hl", "sub": ""},
        {"label": "门槛 II", "value": summary["ii"], "css_class": "", "sub": ""},
        {"label": "仓位建议", "value": summary["verdict"], "css_class": "warn" if any(k in summary['verdict'] for k in ['不建仓', '排除']) else ('highlight' if '买入' in summary['verdict'] else 'amber-hl'), "sub": summary["margin"]},
    ]

    html = Environment(loader=BaseLoader()).from_string(template_text).render(
        company_name=header["company_name"],
        stock_code=header["stock_code"],
        generated_date=header["date"],
        verdict_class=verdict_class,
        verdict_tag_class=verdict_tag_class,
        verdict_tag=summary["verdict"] or "N/A",
        verdict_text=f"GG {summary['gg']} vs 门槛 {summary['ii']}，价值陷阱 {summary['trap']}，可信度 {summary['credibility']}" if summary["gg"] else summary["verdict"],
        key_cards=key_cards,
        meta_html=meta_html,
        exec_html=exec_html,
        assumptions_html=assumptions_html,
        trends_html=trends_html,
        quality_html=quality_html,
        quant_html=quant_html,
        valuation_html=valuation_html,
        conclusion_html=conclusion_html,
        thesis_html=thesis_html,
        standalone_css=_FALLBACK_CSS if args.standalone else "",
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"HTML report generated: {output_path}")
    print(f"  Has executive summary: {bool(exec_html)}")
    print(f"  Has assumptions: {bool(assumptions_html)}")
    print(f"  Has quantitative summary: {bool(quant_html)}")
    print(f"  Has quality section: {bool(quality_html)}")
    print(f"  Has risk/thesis section: {bool(thesis_html)}")


if __name__ == "__main__":
    main()
