#!/usr/bin/env python3
"""Deterministically pre-compute error-prone qualitative-report metrics.

``data_pack_market.md`` stores A-share financial tables in millions.  This
module converts the small, high-risk arithmetic surface into a generated
``computed_metrics.md`` budget so the report writer can cite values instead of
recomputing unit conversions, growth rates, payout ratios, and PE scenarios.

The module supports both invocation styles::

    python scripts/quality_control.py --input ... --output ...
    python -m scripts.quality_control --input ... --output ...

Exit codes: 0 success; 2 missing or unparseable input.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path
from typing import Optional

if __package__:
    from .format_utils import format_header, format_number, format_table
else:
    from format_utils import format_header, format_number, format_table


HEADER_WARNING = (
    "> ⚠️ 以下数值由 Python 确定性计算。报告应直接引用并标注 "
    "`[src: CM§N]`，不要重复心算。百万元→亿元 = 原值 ÷ 100。\n"
)


def to_yi(value_mn: Optional[float]) -> Optional[float]:
    """Convert millions to hundred-millions (亿元)."""
    return None if value_mn is None else value_mn / 100.0


def multi_year_stats(values: list[Optional[float]]) -> dict[str, Optional[float] | int]:
    """Return mean, median, and observation count for available values."""
    available = [value for value in values if value is not None]
    if not available:
        return {"mean": None, "median": None, "n": 0}
    return {
        "mean": sum(available) / len(available),
        "median": statistics.median(available),
        "n": len(available),
    }


def payout_ratio(dividend_total: Optional[float], net_profit: Optional[float]) -> Optional[float]:
    """Dividend payout ratio in percent."""
    if dividend_total is None or net_profit in (None, 0):
        return None
    return dividend_total / net_profit * 100.0


def yoy_pct(current: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Year-over-year change in percent; negative bases retain their sign-safe denominator."""
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / abs(previous) * 100.0


def pe_valuation(eps: Optional[float], pe: Optional[float], discount: Optional[float]) -> Optional[float]:
    """Target price = EPS × PE × discount."""
    if eps is None or pe is None or discount is None:
        return None
    return eps * pe * discount


def _num(cell: Optional[str]) -> Optional[float]:
    """Parse a numeric markdown cell while tolerating annotations and missing markers."""
    if cell is None:
        return None
    cleaned = cell.strip().replace(",", "").replace("†", "").replace("*", "")
    cleaned = cleaned.split("(", 1)[0].split("（", 1)[0].strip()
    if cleaned in {"", "—", "-", "–", "N/A", "null"}:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _rows(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows


def _is_separator(row: list[str]) -> bool:
    return bool(row) and all(set(cell) <= set("-: ") for cell in row)


def parse_sections(text: str) -> dict[str, str]:
    """Split a data pack into blocks keyed by section token (for example ``3P``)."""
    pattern = re.compile(r"^##\s+(\d+[A-Za-z]?)\.\s", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start():end]
    return sections


def parse_matrix(block: str) -> tuple[list[str], dict[str, dict[str, Optional[float]]]]:
    """Parse an item-by-period markdown table."""
    rows = [row for row in _rows(block) if not _is_separator(row)]
    if len(rows) < 2:
        return [], {}
    periods = rows[0][1:]
    data: dict[str, dict[str, Optional[float]]] = {}
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        data[row[0]] = {
            period: _num(row[index + 1] if index + 1 < len(row) else None)
            for index, period in enumerate(periods)
        }
    return periods, data


def parse_kv(block: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _rows(block):
        if not _is_separator(row) and len(row) >= 2:
            result[row[0]] = row[1]
    return result


def find_item(data: dict[str, dict[str, Optional[float]]], *names: str) -> Optional[str]:
    """Find a row by preferred prefix first, then by containment."""
    for name in names:
        for key in data:
            if key.replace(" ", "").startswith(name):
                return key
    for name in names:
        for key in data:
            if name in key:
                return key
    return None


def _series(
    data: dict[str, dict[str, Optional[float]]],
    item_key: Optional[str],
    periods: list[str],
) -> list[Optional[float]]:
    row = data.get(item_key, {}) if item_key else {}
    return [row.get(period) for period in periods]


def _full_years(periods: list[str], limit: int = 5) -> list[str]:
    return [period for period in periods if re.fullmatch(r"\d{4}", period)][:limit]


def _yi_cells(values: list[Optional[float]]) -> list[str]:
    return [format_number(to_yi(value), divider=1) for value in values]


def _dividends_by_year(block: str) -> dict[str, float]:
    """Aggregate multiple dividend rows belonging to the same reporting year."""
    rows = [row for row in _rows(block) if not _is_separator(row)]
    if len(rows) < 2:
        return {}
    header = rows[0]
    dividend_index = next(
        (index for index, heading in enumerate(header) if "总分红" in heading),
        len(header) - 1,
    )
    totals: dict[str, float] = {}
    for row in rows[1:]:
        year = row[0].strip()
        if not re.fullmatch(r"\d{4}", year):
            continue
        value = _num(row[dividend_index] if dividend_index < len(row) else None)
        if value is not None:
            totals[year] = totals.get(year, 0.0) + value
    return totals


def build_report(
    sections: dict[str, str],
    pe_bands: list[float],
    discounts: list[float],
) -> str:
    """Render the deterministic CM§1-CM§5 metric budget."""
    parts: list[str] = [
        "# 计算结果 — computed_metrics.md（Python 确定性预算）\n",
        HEADER_WARNING,
    ]

    income_periods, income = parse_matrix(sections.get("3", ""))
    _, balance = parse_matrix(sections.get("4", ""))
    _, cashflow = parse_matrix(sections.get("5", ""))
    indicator_periods, indicators = parse_matrix(sections.get("12", ""))
    basics = parse_kv(sections.get("1", ""))
    years = _full_years(income_periods)

    parts.append(format_header(2, "CM§1 亿元对照表（百万元 ÷ 100 = 亿元）"))
    if not years:
        parts.append("> ⚠️ CM§1 跳过：缺少 §3 利润表年度数据。\n")
    else:
        latest = years[0]
        specs = [
            ("营业收入", income, ("营业收入",)),
            ("营业利润", income, ("营业利润",)),
            ("净利润", income, ("净利润",)),
            ("归母净利润", income, ("归母净利润",)),
            ("总资产", balance, ("总资产",)),
            ("归母所有者权益", balance, ("归母所有者权益", "归母权益")),
            ("经营活动现金流(OCF)", cashflow, ("经营活动现金流", "OCF")),
            ("自由现金流(FCF)", cashflow, ("自由现金流", "FCF")),
        ]
        headers = ["项目", f"{latest} 百万元", f"{latest} 亿元"] + [
            f"{year} 亿元" for year in years[1:]
        ]
        rows: list[list[str]] = []
        for label, source, names in specs:
            values = _series(source, find_item(source, *names), years)
            rows.append([label, format_number(values[0], divider=1)] + _yi_cells(values))
        parts.extend([format_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)), ""])

    parts.append(format_header(2, "CM§2 同比变化率（%）"))
    if len(years) < 2:
        parts.append("> ⚠️ CM§2 跳过：可比年度不足 2 年。\n")
    else:
        specs = [
            ("营业收入", ("营业收入",)),
            ("归母净利润", ("归母净利润",)),
            ("净利润", ("净利润",)),
            ("营业利润", ("营业利润",)),
        ]
        headers = ["指标"] + [
            f"{years[index]} vs {years[index + 1]}" for index in range(len(years) - 1)
        ]
        rows = []
        for label, names in specs:
            values = _series(income, find_item(income, *names), years)
            cells = [
                format_number(yoy_pct(values[index], values[index + 1]), divider=1)
                for index in range(len(years) - 1)
            ]
            rows.append([label] + cells)
        parts.extend([format_table(headers, rows, ["l"] + ["r"] * (len(headers) - 1)), ""])

    parts.append(format_header(2, "CM§3 多年统计（均值 / 中位数）"))
    if not years:
        parts.append("> ⚠️ CM§3 跳过：缺少年度序列。\n")
    else:
        indicator_years = _full_years(indicator_periods)
        specs = [
            ("营业收入(亿元)", [to_yi(value) for value in _series(income, find_item(income, "营业收入"), years)]),
            ("归母净利润(亿元)", [to_yi(value) for value in _series(income, find_item(income, "归母净利润"), years)]),
            ("ROE(%)", _series(indicators, find_item(indicators, "ROE", "净资产收益率"), indicator_years)),
            ("毛利率(%)", _series(indicators, find_item(indicators, "毛利率"), indicator_years)),
            ("净利率(%)", _series(indicators, find_item(indicators, "净利率"), indicator_years)),
        ]
        rows = []
        for label, values in specs:
            stats = multi_year_stats(values)
            rows.append([
                label,
                format_number(stats["mean"], divider=1),
                format_number(stats["median"], divider=1),
                str(stats["n"]),
            ])
        parts.extend([format_table(["指标", "均值", "中位数", "年数"], rows, ["l", "r", "r", "r"]), ""])

    parts.append(format_header(2, "CM§4 分红支付率（总分红 ÷ 归母净利润）"))
    dividends = _dividends_by_year(sections.get("6", ""))
    net_profit_key = find_item(income, "归母净利润")
    if not dividends or not net_profit_key:
        parts.append("> ⚠️ CM§4 跳过：缺少 §6 分红或 §3 归母净利润。\n")
    else:
        rows = []
        for year in sorted(dividends, reverse=True):
            dividend = dividends[year]
            net_profit = income.get(net_profit_key, {}).get(year)
            rows.append([
                year,
                format_number(to_yi(dividend), divider=1),
                format_number(to_yi(net_profit), divider=1),
                format_number(payout_ratio(dividend, net_profit), divider=1),
            ])
        parts.extend([
            format_table(
                ["年度", "总分红(亿元)", "归母净利润(亿元)", "支付率(%)"],
                rows,
                ["l", "r", "r", "r"],
            ),
            "",
        ])

    parts.append(format_header(2, "CM§5 PE 估值链网格（目标价 = EPS × PE × 折扣）"))
    eps_key = find_item(income, "基本EPS", "基本每股收益", "EPS")
    eps = income.get(eps_key, {}).get(years[0]) if eps_key and years else None
    price = _num(basics.get("当前价格"))
    market_cap_wan = _num(basics.get("总市值 (万元)")) or _num(basics.get("总市值(万元)"))
    if eps is None:
        parts.append("> ⚠️ CM§5 跳过：缺少 §3 基本EPS。\n")
    else:
        note = f"> EPS = {years[0]} 基本EPS = {format_number(eps, divider=1)} 元"
        if price is not None:
            note += f"；当前股价 = {format_number(price, divider=1)} 元"
        if market_cap_wan is not None:
            note += f"；总市值 = {format_number(market_cap_wan / 10000.0, divider=1)} 亿元（§1 万元 ÷ 10000）"
        parts.append(note + "\n")
        headers = ["PE \\ 折扣"] + [f"×{discount:g}" for discount in discounts]
        rows = [
            [f"PE {pe:g}"] + [
                format_number(pe_valuation(eps, pe, discount), divider=1)
                for discount in discounts
            ]
            for pe in pe_bands
        ]
        parts.extend([format_table(headers, rows, ["l"] + ["r"] * len(discounts)), ""])

    parts.append(
        "---\n*computed_metrics.md · 由 scripts/quality_control.py 生成 · 内部工件（非交付物）*"
    )
    return "\n".join(parts) + "\n"


def _parse_floats(value: str) -> list[float]:
    return [float(item) for item in value.split(",") if item.strip()]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="预算定性报告易错指标 → computed_metrics.md")
    parser.add_argument("--input", required=True, help="data_pack_market.md 路径")
    parser.add_argument("--output", required=True, help="computed_metrics.md 输出路径")
    parser.add_argument("--pe-bands", default="10,15,20,25,30", help="PE 档位，逗号分隔")
    parser.add_argument("--discounts", default="1.0,0.9,0.8,0.7", help="折扣系数，逗号分隔")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        print(f"[quality_control] 输入文件不存在: {input_path}", file=sys.stderr)
        return 2

    sections = parse_sections(input_path.read_text(encoding="utf-8"))
    if not sections:
        print("[quality_control] 无法解析任何数据板块（§N）。", file=sys.stderr)
        return 2

    try:
        report = build_report(
            sections,
            _parse_floats(args.pe_bands),
            _parse_floats(args.discounts),
        )
    except ValueError as exc:
        print(f"[quality_control] 参数解析失败: {exc}", file=sys.stderr)
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"[quality_control] 已写入 {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
