#!/usr/bin/env python3
"""Advisory cross-passage numeric consistency audit for qualitative reports.

The scanner groups money and ratio observations by metric and year, normalizes
money to 亿元, and reports materially different values used for the same key.
Its exit-1 result is deliberately advisory: period or accounting-scope
differences require human/agent adjudication, while ``validate_reports.py``
remains the repository's authoritative delivery contract.

Exit codes: 0 no conflicts; 1 potential conflicts; 2 file error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


WINDOW = 40
CATEGORIES: list[tuple[str, tuple[str, ...], str]] = [
    ("扣非净利润", ("扣非净利润", "扣非归母", "扣非"), "money"),
    ("归母净利润", ("归母净利润", "归母"), "money"),
    ("营业利润", ("营业利润",), "money"),
    ("净利润", ("净利润",), "money"),
    ("营业收入", ("营业收入", "营收", "销售收入"), "money"),
    ("营业成本", ("营业成本",), "money"),
    ("总市值", ("总市值", "市值"), "money"),
    ("分红总额", ("总分红", "分红总额", "现金分红总额"), "money"),
    ("毛利率", ("毛利率",), "ratio"),
    ("净利率", ("净利率",), "ratio"),
    ("ROE", ("ROE", "净资产收益率", "加权roe"), "ratio"),
    ("资产负债率", ("资产负债率",), "ratio"),
    ("股息率", ("股息率",), "ratio"),
    ("分红支付率", ("分红支付率", "分红率", "支付率", "派息率"), "ratio"),
]
MONEY_UNITS = {
    "万亿元": 10000.0,
    "万亿": 10000.0,
    "亿元": 1.0,
    "亿": 1.0,
    "百万元": 0.01,
    "百万": 0.01,
    "万元": 0.0001,
}
NUM_UNIT_RE = re.compile(
    r"(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)\s*"
    r"(万亿元|万亿|亿元|百万元|万元|亿|百万|%|％)"
)
YEAR_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})(?!\d)")
MASK_PATTERNS = [
    re.compile(r"\[src:[^\]]*\]", re.IGNORECASE),
    re.compile(r"§\s*\d+(?:\.\d+)?"),
    re.compile(r"[Pp]\.?\s*\d+"),
    re.compile(r"\d{8}"),
    re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}"),
]


@dataclass(frozen=True)
class Observation:
    value: float
    line: int
    snippet: str


def _mask(text: str) -> str:
    """Blank source tags, section/page pointers, and full dates while preserving offsets."""
    result = list(text)
    for pattern in MASK_PATTERNS:
        for match in pattern.finditer(text):
            result[match.start():match.end()] = " " * (match.end() - match.start())
    return "".join(result)


def _classify(window: str, number_offset: int) -> Optional[tuple[str, str]]:
    """Choose the nearest metric keyword to avoid adjacent-metric contamination."""
    lowered = window.lower()
    best: Optional[tuple[int, str, str]] = None
    for canonical, keywords, kind in CATEGORIES:
        for keyword in keywords:
            haystack = lowered if keyword.islower() else window
            start = 0
            while True:
                index = haystack.find(keyword, start)
                if index < 0:
                    break
                keyword_end = index + len(keyword)
                if keyword_end <= number_offset:
                    distance = number_offset - keyword_end
                elif index >= number_offset:
                    distance = index - number_offset
                else:
                    distance = 0
                if best is None or distance < best[0]:
                    best = (distance, canonical, kind)
                start = index + 1
    return None if best is None else (best[1], best[2])


def _nearest_year(window: str, number_offset: int) -> Optional[str]:
    matches = list(YEAR_RE.finditer(window))
    if not matches:
        return None
    # In financial prose a year normally opens a clause and applies to the
    # values that follow until another year appears.  Prefer the latest prior
    # year; only fall back to a following year for inverted phrasing.
    preceding = [match for match in matches if match.start() <= number_offset]
    if preceding:
        return max(preceding, key=lambda match: match.start()).group(1)
    return min(matches, key=lambda match: match.start()).group(1)


def _line_of(text: str, position: int) -> int:
    return text.count("\n", 0, position) + 1


def extract(text: str) -> dict[tuple[str, str], list[Observation]]:
    """Extract normalized observations keyed by ``(metric, year)``."""
    masked = _mask(text)
    clusters: dict[tuple[str, str], list[Observation]] = {}
    for match in NUM_UNIT_RE.finditer(masked):
        raw, unit = match.group(1), match.group(2)
        try:
            value = float(raw.replace(",", ""))
        except ValueError:
            continue
        start = max(0, match.start() - WINDOW)
        end = min(len(masked), match.end() + WINDOW)
        window = masked[start:end]
        number_offset = match.start() - start
        classification = _classify(window, number_offset)
        year = _nearest_year(window, number_offset)
        if classification is None or year is None:
            continue
        canonical, kind = classification
        if kind == "money":
            if unit not in MONEY_UNITS:
                continue
            normalized = value * MONEY_UNITS[unit]
        else:
            if unit not in {"%", "％"}:
                continue
            normalized = value
        snippet = re.sub(r"\s+", " ", text[start:end]).strip()
        clusters.setdefault((canonical, year), []).append(
            Observation(normalized, _line_of(text, match.start()), snippet)
        )
    return clusters


def _distinct_groups(values: list[float], tolerance: float) -> list[float]:
    representatives: list[float] = []
    for value in sorted(values):
        if not any(
            abs(value - representative) / max(abs(value), abs(representative), 1e-9)
            <= tolerance
            for representative in representatives
        ):
            representatives.append(value)
    return representatives


def find_conflicts(
    clusters: dict[tuple[str, str], list[Observation]],
    tolerance: float,
) -> list[dict[str, object]]:
    """Find clusters containing more than one tolerance-distinct value."""
    conflicts: list[dict[str, object]] = []
    for (category, year), observations in clusters.items():
        values = [observation.value for observation in observations]
        if len(_distinct_groups(values, tolerance)) < 2:
            continue
        spread = (max(values) - min(values)) / max(abs(max(values)), abs(min(values)), 1e-9)
        conflicts.append({
            "category": category,
            "year": year,
            "spread": spread,
            "values": sorted({round(value, 4) for value in values}),
            "locations": sorted({observation.line for observation in observations}),
            "observations": observations,
        })
    conflicts.sort(key=lambda conflict: (-float(conflict["spread"]), str(conflict["category"])))
    return conflicts


def render(conflicts: list[dict[str, object]], tolerance: float) -> str:
    lines = [
        "# 一致性审计 — consistency_report.md\n",
        f"> 容差 {tolerance:.0%}；结果仅为 **advisory**。真错误与口径/期间差异须由数字审计裁定，最终交付仍以本地 report_contract/validate_reports 为准。\n",
        "## 跨段数值冲突\n",
    ]
    if not conflicts:
        lines.append("✅ 未发现跨段数值冲突。\n")
    else:
        lines.extend([
            f"发现 **{len(conflicts)}** 处潜在冲突：\n",
            "| 指标 | 年份 | 冲突数值 | 相对差 | 出现行号 |",
            "| --- | --- | --- | ---: | --- |",
        ])
        for conflict in conflicts:
            values = " / ".join(f"{value:g}" for value in conflict["values"])
            locations = ", ".join(str(line) for line in conflict["locations"])
            lines.append(
                f"| {conflict['category']} | {conflict['year']} | {values} | "
                f"{float(conflict['spread']):.1%} | {locations} |"
            )
        lines.append("")
    lines.append(
        "---\n*consistency_report.md · 由 scripts/report_consistency.py 生成 · 内部工件（非交付物）*"
    )
    return "\n".join(lines) + "\n"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="定性报告跨段数字一致性审计（提示性）")
    parser.add_argument("--report", required=True, help="定性报告 Markdown 路径")
    parser.add_argument("--output", help="consistency_report.md 输出路径；省略则打印到 stdout")
    parser.add_argument("--tolerance", type=float, default=0.05, help="相对容差，默认 0.05")
    args = parser.parse_args(argv)

    report_path = Path(args.report)
    if not report_path.is_file():
        print(f"[report_consistency] 文件不存在: {report_path}", file=sys.stderr)
        return 2
    text = report_path.read_text(encoding="utf-8")
    if not text.strip():
        print("[report_consistency] 报告为空。", file=sys.stderr)
        return 2
    if args.tolerance < 0:
        print("[report_consistency] tolerance 不能为负数。", file=sys.stderr)
        return 2

    conflicts = find_conflicts(extract(text), args.tolerance)
    rendered = render(conflicts, args.tolerance)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    print(f"[report_consistency] 潜在冲突 {len(conflicts)} 处", file=sys.stderr)
    return 1 if conflicts else 0


if __name__ == "__main__":
    raise SystemExit(main())
