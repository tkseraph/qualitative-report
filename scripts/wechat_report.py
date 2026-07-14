#!/usr/bin/env python3
"""Create WeChat Official Account drafts from finished Markdown reports."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from pathlib import Path
from typing import NamedTuple

if __package__:
    from .validate_reports import validate_file
    from .report_to_html import render_report_html
else:
    from validate_reports import validate_file
    from report_to_html import render_report_html

REPORT_TYPES = ("qualitative", "turtle", "valuation")
CREDENTIAL_LIKE_ARGS = {"--appid", "--appsecret", "--secret", "--token"}


class FinancialSeries(NamedTuple):
    years: list[str]
    revenue: list[float]
    net_profit: list[float]
    fcf: list[float]
    roe: list[float]
    operating_cash_flow: list[float]
    gross_margin: list[float]
    receivables: list[float]
    inventory: list[float]


def discover_report(path: Path, report_type: str | None, explicit_file: Path | None) -> Path:
    if explicit_file is not None:
        if not explicit_file.exists():
            raise SystemExit(f"Report file not found: {explicit_file}")
        return explicit_file
    if path.is_file():
        if path.suffix.lower() != ".md":
            raise SystemExit(f"Expected a Markdown report file: {path}")
        return path
    if not path.exists():
        raise SystemExit(f"Path not found: {path}")
    if report_type is None:
        raise SystemExit("--type is required when path is an output directory")
    matches = sorted(path.glob(f"*_{report_type}_report.md"))
    if not matches:
        raise SystemExit(f"Missing {report_type} report in: {path}")
    if len(matches) > 1:
        raise SystemExit(
            f"Multiple {report_type} reports found; keep exactly one: "
            + ", ".join(str(match) for match in matches)
        )
    return matches[0]


def infer_report_type(report_path: Path) -> str:
    for report_type in REPORT_TYPES:
        if report_path.name.endswith(f"_{report_type}_report.md"):
            return report_type
    known = ", ".join(f"*_{report_type}_report.md" for report_type in REPORT_TYPES)
    raise SystemExit(f"Cannot infer report type from filename: {report_path.name}. Expected: {known}")


def validate_before_draft(report_path: Path, report_type: str) -> None:
    result = validate_file(report_path, report_type)
    if not result.ok:
        messages = "\n".join(f"- {message}" for message in result.messages)
        raise SystemExit(f"Report validation failed: {report_path}\n{messages}")


def _section_body(md_text: str, title_keywords: tuple[str, ...]) -> str:
    sections = re.split(r"(?=^## )", md_text, flags=re.MULTILINE)
    for section in sections:
        header_match = re.match(r"##\s+(.+?)(?:\n|$)", section)
        if not header_match:
            continue
        title = header_match.group(1)
        if any(keyword in title for keyword in title_keywords):
            return section[header_match.end():].strip()
    return ""


def _first_sentence(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    compact = re.sub(r"^[-*>#\s]+", "", compact)
    match = re.search(r"^(.+?[。！？.!?])", compact)
    return match.group(1).strip() if match else compact


def _trim_digest(text: str, max_chars: int = 80) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    compact = re.sub(r"^(?:一句话摘要|一句话判断|一句话结论|摘要)[：:]\s*", "", compact)
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip("，,。；;、 ") + "…"


def auto_digest_from_qualitative(md_text: str) -> str:
    summary = _section_body(md_text, ("Executive Summary", "执行摘要"))
    if summary:
        first = _first_sentence(summary)
        if first:
            return _trim_digest(first)

    verdict = _section_body(md_text, ("Business Quality Verdict", "商业质量总体评级"))
    if verdict:
        first = _first_sentence(verdict)
        if first:
            return _trim_digest(first)

    title_match = re.search(r"^#\s+(.+?)(?:—|-|$)", md_text, flags=re.MULTILINE)
    if title_match:
        return _trim_digest(f"{title_match.group(1).strip()}商业质量定性分析")
    return "商业质量定性分析"


WECHAT_LABELS = {
    "moat_rating": "护城河评级",
    "moat_sustainability": "护城河可持续性",
    "management_rating": "管理层评价",
    "cyclicality": "周期属性",
    "cycle_position": "周期位置",
    "capital_intensity": "资本强度",
    "entry_barrier": "进入壁垒",
    "moat_existence": "护城河存在性",
    "roe_5y_avg": "五年平均 ROE",
}


def _clean_card_value(value: str) -> str:
    return re.sub(r"[*`]+", "", value).strip()


def _wechat_label(value: str) -> str:
    cleaned = _clean_card_value(value)
    return WECHAT_LABELS.get(cleaned, cleaned)


def _extract_card_value(md_text: str, keywords: tuple[str, ...], fallback: str = "见正文") -> str:
    for keyword in keywords:
        pattern = rf"(?:{re.escape(keyword)})[：:]\s*(.+)$"
        match = re.search(pattern, md_text, flags=re.MULTILINE)
        if not match:
            continue
        raw_value = match.group(1).strip()
        emphasized = re.match(r"^(\*\*|\*)(.+?)\1", raw_value)
        value = emphasized.group(2) if emphasized else _first_sentence(raw_value)
        value = _clean_card_value(value)
        if value:
            return _trim_digest(value, 80)
    return fallback


def _first_screen_table_values(md_text: str) -> dict[str, str]:
    lines = md_text.splitlines()
    for index in range(len(lines)):
        parsed = _parse_markdown_table(lines, index)
        if parsed is None:
            continue
        headers, rows, _ = parsed
        if not _is_first_screen_summary_table(headers, rows):
            continue
        values = {_clean_card_value(row[0]): _trim_digest(_clean_card_value(row[1]), 100) for row in rows if len(row) >= 2}
        return {
            "company_essence": values.get("公司本质", ""),
            "quality": values.get("商业质量", ""),
            "moat": values.get("护城河来源", ""),
            "risk": values.get("最大风险", ""),
            "cycle": values.get("周期位置", ""),
            "refutation": values.get("反证条件", ""),
        }
    return {}


def _first_screen_values(md_text: str) -> dict[str, str]:
    table_values = _first_screen_table_values(md_text)
    return {
        "company_essence": table_values.get("company_essence") or _extract_card_value(md_text, ("公司本质",), _trim_digest(auto_digest_from_qualitative(md_text), 80)),
        "quality": table_values.get("quality") or _extract_card_value(md_text, ("商业质量", "综合判断", "总体评级"), "见 Business Quality Verdict"),
        "moat": table_values.get("moat") or _extract_card_value(md_text, ("护城河来源", "核心优势", "优势来自"), "见维度二"),
        "risk": table_values.get("risk") or _extract_card_value(md_text, ("最大风险", "核心风险", "主要风险", "主要约束"), "见核心矛盾"),
        "cycle": table_values.get("cycle") or _extract_card_value(md_text, ("周期位置", "当前周期"), "不适用 / 见外部环境"),
        "refutation": table_values.get("refutation") or _extract_card_value(md_text, ("反证条件", "重评触发", "重评动作"), "见核心矛盾与未来观察变量"),
    }


def _first_screen_card(md_text: str) -> str:
    values = _first_screen_values(md_text)
    return "\n".join([
        "| 项目 | 结论 |",
        "|---|---|",
        f"| 公司本质 | {values['company_essence']} |",
        f"| 商业质量 | {values['quality']} |",
        f"| 护城河来源 | {values['moat']} |",
        f"| 最大风险 | {values['risk']} |",
        f"| 周期位置 | {values['cycle']} |",
        f"| 反证条件 | {values['refutation']} |",
    ])


def _wechat_hero_card(md_text: str) -> str:
    values = _first_screen_values(md_text)
    conclusion = _trim_digest(auto_digest_from_qualitative(md_text), 140)
    return "\n".join([
        "## 一句话结论",
        "",
        f"> {conclusion}",
        "",
        f"**质量评级**：{values['quality']}  ",
        f"**公司本质**：{values['company_essence']}  ",
        f"**护城河来源**：{values['moat']}  ",
        f"**最大风险**：{values['risk']}  ",
        f"**周期位置**：{values['cycle']}  ",
        f"**未来最该看**：{values['refutation']}",
    ])


def _has_first_screen_card(md_text: str) -> bool:
    hero_markers = all(marker in md_text for marker in (
        "## 一句话结论",
        "质量评级",
        "公司本质",
        "护城河来源",
        "最大风险",
        "未来最该看",
    ))
    if hero_markers:
        return True
    mobile_markers = all(marker in md_text for marker in (
        "### 公司本质",
        "### 商业质量",
        "### 护城河来源",
        "### 最大风险",
    ))
    if mobile_markers:
        return True
    card_heading = re.search(r"^#{2,4}\s+首屏摘要卡\s*$", md_text, flags=re.MULTILINE)
    has_required_rows = all(marker in md_text for marker in (
        "| 公司本质 |",
        "| 商业质量 |",
        "| 护城河来源 |",
        "| 最大风险 |",
    ))
    if card_heading and has_required_rows:
        return True
    return all(marker in md_text for marker in (
        "| 项目 | 结论 |",
        "| 公司本质 |",
        "| 商业质量 |",
        "| 护城河来源 |",
        "| 最大风险 |",
    ))


def _is_markdown_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _parse_markdown_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int] | None:
    if start + 1 >= len(lines) or not lines[start].strip().startswith("|"):
        return None
    if not _is_markdown_table_separator(lines[start + 1]):
        return None
    headers = [cell.strip() for cell in lines[start].strip().strip("|").split("|")]
    rows: list[list[str]] = []
    index = start + 2
    while index < len(lines) and lines[index].strip().startswith("|"):
        if not _is_markdown_table_separator(lines[index]):
            cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
            if cells:
                rows.append(cells)
        index += 1
    if not headers or not rows:
        return None
    return headers, rows, index


def _table_to_mobile_blocks(headers: list[str], rows: list[list[str]]) -> list[str]:
    blocks: list[str] = []
    use_heading_title = len(rows) <= 3
    for row in rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        title = _wechat_label(padded[0]) or "表格项目"
        blocks.append(f"### {title}" if use_heading_title else f"**{title}**")
        for header, value in zip(headers[1:], padded[1:]):
            clean_header = _wechat_label(header)
            clean_value = _clean_card_value(value)
            if clean_header and clean_value:
                blocks.append(f"- **{clean_header}**：{clean_value}")
        blocks.append("")
    return blocks[:-1] if blocks and blocks[-1] == "" else blocks


def _is_first_screen_summary_table(headers: list[str], rows: list[list[str]]) -> bool:
    row_names = {_clean_card_value(row[0]) for row in rows if row}
    return (
        len(headers) == 2
        and _clean_card_value(headers[0]) in {"项目", "问题"}
        and _clean_card_value(headers[1]) in {"结论", "回答"}
        and {"公司本质", "商业质量", "护城河来源", "最大风险"}.issubset(row_names)
    )


def _remove_verdict_body_before_hero(md_text: str) -> str:
    marker = re.search(r"^## 一句话结论\s*$", md_text, flags=re.MULTILINE)
    if marker is None:
        return md_text
    before = md_text[:marker.start()]
    after = md_text[marker.start():]
    verdict = re.search(r"(^##\s+.*?(?:Business Quality Verdict|商业质量总体评级).*?\n)", before, flags=re.MULTILINE)
    if verdict is None:
        return md_text
    return before[:verdict.end()].rstrip() + "\n\n" + after.lstrip()


def _replace_first_screen_table_with_hero(md_text: str) -> str:
    lines = md_text.splitlines()
    output: list[str] = []
    in_code_fence = False
    index = 0
    inserted = False
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            output.append(lines[index])
            index += 1
            continue
        if not in_code_fence and not inserted:
            parsed = _parse_markdown_table(lines, index)
            if parsed is not None:
                headers, rows, next_index = parsed
                if _is_first_screen_summary_table(headers, rows):
                    output.extend(_wechat_hero_card(md_text).splitlines())
                    inserted = True
                    index = next_index
                    continue
        output.append(lines[index])
        index += 1
    if inserted:
        return _remove_verdict_body_before_hero("\n".join(output))
    return md_text


def _format_markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    normalized_rows = [row + [""] * max(0, len(headers) - len(row)) for row in rows]
    return [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row[:len(headers)]) + " |" for row in normalized_rows),
    ]


def _is_narrow_judgment_table(headers: list[str], rows: list[list[str]]) -> bool:
    if len(headers) > 4 or len(rows) > 6:
        return False
    cleaned_headers = [_clean_card_value(header) for header in headers]
    if _is_first_screen_summary_table(headers, rows) or cleaned_headers in (["项目", "结论"], ["问题", "回答"]):
        return False
    has_judgment_column = any(header in {"判断", "商业含义", "投资含义", "结论"} for header in cleaned_headers)
    max_cell_length = max((len(_clean_card_value(cell)) for row in rows for cell in row), default=0)
    return has_judgment_column and max_cell_length <= 24


def _convert_markdown_tables_for_wechat(md_text: str) -> str:
    lines = md_text.splitlines()
    output: list[str] = []
    in_code_fence = False
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            output.append(lines[index])
            index += 1
            continue
        if not in_code_fence:
            parsed = _parse_markdown_table(lines, index)
            if parsed is not None:
                headers, rows, next_index = parsed
                if _is_narrow_judgment_table(headers, rows):
                    output.extend(_format_markdown_table(headers, rows))
                else:
                    output.extend(_table_to_mobile_blocks(headers, rows))
                index = next_index
                continue
        output.append(lines[index])
        index += 1
    return "\n".join(output)


def _remove_local_data_boundary(md_text: str) -> str:
    lines = [line for line in md_text.splitlines() if "数据边界" not in line]
    return "\n".join(lines)


def _sanitize_local_source_mentions(md_text: str) -> str:
    replacements = {
        r"`?data_pack_market\.md`?": "Tushare 数据",
        r"`?annual_report\.pdf`?": "上市公司年报",
        r"`?pdf_sections\.json`?": "年报抽取信息",
        r"`?data_pack_report\.md`?": "年报附注抽取信息",
        r"shared/qualitative/[\w./-]+": "定性分析框架",
        r"output/[\w./-]+": "本地分析材料",
        r"年度报告 PDF": "公司年报",
        r"年报 PDF": "公司年报",
        r"本地 Tushare 数据包": "Tushare 财务及市场数据",
        r"本地 Tushare 数据": "Tushare 财务及市场数据",
        r"Tushare 数据包": "Tushare 财务及市场数据",
        r"PDF 附注抽取文件": "年报附注",
        r"本地数据包": "Tushare 财务及市场数据",
        r"本地证据": "当前证据",
        r"本地输入": "公开资料",
    }
    sanitized = md_text
    for pattern, replacement in replacements.items():
        sanitized = re.sub(pattern, replacement, sanitized)
    sanitized = re.sub(
        r"核心数据来源：.*(?:公司年报|上市公司年报|Tushare|年报附注).*",
        "核心数据来源：公司年报、年报附注与 Tushare 财务及市场数据。",
        sanitized,
    )
    return sanitized


def _remove_section(md_text: str, heading_keywords: tuple[str, ...]) -> str:
    lines = md_text.splitlines()
    output: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#{2,4}\s+", stripped):
            skipping = any(keyword in stripped for keyword in heading_keywords)
            if skipping:
                continue
        if not skipping:
            output.append(line)
    return "\n".join(output)


def _is_machine_field_table(headers: list[str], rows: list[list[str]]) -> bool:
    field_names = {"roe_5y_avg", *WECHAT_LABELS.keys()}
    row_names = {_clean_card_value(row[0]) for row in rows if row}
    return bool(row_names & field_names) and len(row_names & field_names) >= min(2, len(row_names))


def _remove_machine_field_tables(md_text: str) -> str:
    lines = md_text.splitlines()
    output: list[str] = []
    in_code_fence = False
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            output.append(lines[index])
            index += 1
            continue
        if not in_code_fence:
            parsed = _parse_markdown_table(lines, index)
            if parsed is not None:
                headers, rows, next_index = parsed
                if _is_machine_field_table(headers, rows):
                    index = next_index
                    continue
        output.append(lines[index])
        index += 1
    return "\n".join(output)


def _simplify_wechat_data_sources(md_text: str) -> str:
    lines = md_text.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if re.match(r"^##\s+.*数据来源", stripped):
            output.append(line)
            output.append("")
            output.append("基于上市公司年报和 Tushare 数据。")
            index += 1
            while index < len(lines) and not re.match(r"^##\s+", lines[index].strip()):
                index += 1
            continue
        output.append(line)
        index += 1
    return "\n".join(output)


def _split_long_body_line(line: str, max_chars: int = 100) -> list[str]:
    stripped = line.strip()
    if len(stripped) <= max_chars:
        return [line]
    parts = re.split(r"(?<=[。！？；;，,、])", stripped)
    chunks: list[str] = []
    current = ""
    for part in parts:
        if not part:
            continue
        if current and len(current) + len(part) > max_chars:
            chunks.append(current)
            current = part
        else:
            current += part
    if current:
        chunks.append(current)
    return chunks or [line]


def _split_overlong_body_lines(md_text: str, max_chars: int = 100) -> str:
    lines: list[str] = []
    in_code_fence = False
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            lines.append(line)
            continue
        if (
            in_code_fence
            or not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith(">")
            or len(stripped) <= max_chars
        ):
            lines.append(line)
            continue
        lines.extend(_split_long_body_line(line, max_chars))
    return "\n".join(lines)


def _add_wechat_section_dividers(md_text: str) -> str:
    divider_titles = (
        "Executive Summary",
        "执行摘要",
        "维度一",
        "维度二",
        "维度三",
        "维度四",
        "维度五",
        "维度六",
        "D1",
        "D2",
        "D3",
        "D4",
        "D5",
        "D6",
        "深度总结",
        "未来观察",
        "数据来源",
        "免责声明",
        "结构化参数",
    )
    lines = md_text.splitlines()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        should_divide = stripped.startswith("## ") and any(title in stripped for title in divider_titles)
        if should_divide:
            previous_nonempty = next((item.strip() for item in reversed(output) if item.strip()), "")
            if previous_nonempty != "---":
                if output and output[-1].strip():
                    output.append("")
                output.append("---")
                output.append("")
        output.append(line)
    return "\n".join(output)


def _markdown_image_paths(md_text: str) -> list[str]:
    return [match.group(1).strip() for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", md_text)]


def validate_wechat_draft_readiness(polished_path: Path, preview_path: Path | None = None) -> list[str]:
    md_text = polished_path.read_text(encoding="utf-8")
    issues = validate_wechat_polish_quality(md_text)
    image_paths = _markdown_image_paths(md_text)
    if "## 关键财务趋势图" in md_text and not image_paths:
        issues.append("wechat_chart_section_without_images")
    for image_path in image_paths:
        if re.match(r"https?://", image_path):
            continue
        if not (polished_path.parent / image_path).exists():
            issues.append("wechat_missing_image_asset")
            break
    if preview_path is not None and preview_path.exists():
        html = preview_path.read_text(encoding="utf-8")
        if "<table" in html and ("white-space: nowrap" in html or "tbl-wrapper" in html or "width: max-content" in html):
            issues.append("wechat_preview_table_overflow")
    return issues


def validate_wechat_polish_quality(md_text: str) -> list[str]:
    issues: list[str] = []
    hero_text = md_text.split("## Quality Snapshot", 1)[0]
    required_hero_terms = ("## 一句话结论", "质量评级", "公司本质", "护城河来源", "最大风险", "未来最该看")
    if not all(term in hero_text for term in required_hero_terms):
        issues.append("wechat_hero_card")
    old_mobile_hero_terms = ("### 公司本质", "### 商业质量", "### 护城河来源", "### 最大风险")
    if all(term in hero_text for term in old_mobile_hero_terms):
        issues.append("wechat_heading_stack")
    if "![" in md_text and "**读图结论**" not in md_text:
        issues.append("wechat_chart_reading")
    consecutive_bare_h3 = 0
    previous_heading_has_body = True
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("### "):
            if not previous_heading_has_body:
                consecutive_bare_h3 += 1
            else:
                consecutive_bare_h3 = 1
            previous_heading_has_body = False
            if consecutive_bare_h3 >= 4:
                issues.append("wechat_heading_stack")
                break
            continue
        if stripped and not stripped.startswith("-"):
            previous_heading_has_body = True
            consecutive_bare_h3 = 0
        elif stripped.startswith("-"):
            previous_heading_has_body = True
    return issues


def polish_qualitative_markdown(md_text: str) -> str:
    polished = md_text
    if not _has_first_screen_card(polished):
        verdict_header = re.search(
            r"(^##\s+.*?(?:Business Quality Verdict|商业质量总体评级).*?\n)",
            polished,
            flags=re.MULTILINE,
        )
        if verdict_header:
            insert_at = verdict_header.end()
            polished = polished[:insert_at] + "\n" + _first_screen_card(polished) + "\n\n" + polished[insert_at:]
    polished = _remove_local_data_boundary(polished)
    polished = _sanitize_local_source_mentions(polished)
    polished = _simplify_wechat_data_sources(polished)
    polished = _remove_section(polished, ("结构化参数",))
    polished = _remove_machine_field_tables(polished)
    polished = _replace_first_screen_table_with_hero(polished)
    polished = _convert_markdown_tables_for_wechat(polished)
    polished = _add_wechat_section_dividers(polished)
    polished = _split_overlong_body_lines(polished)
    return polished


def _parse_number(value: str) -> float | None:
    compact = value.replace(",", "").replace("%", "").strip()
    if compact in {"", "—", "-", "--"}:
        return None
    try:
        return float(compact)
    except ValueError:
        return None


def _find_financial_row(md_text: str, label: str) -> tuple[list[str], list[float]] | None:
    lines = md_text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|") or label not in line:
            continue
        header_index = None
        for candidate in range(index - 1, -1, -1):
            if not lines[candidate].strip().startswith("|"):
                break
            if candidate + 1 < len(lines) and _is_markdown_table_separator(lines[candidate + 1]):
                header_index = candidate
                break
        if header_index is None:
            continue
        headers = [cell.strip() for cell in lines[header_index].strip().strip("|").split("|")][1:]
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")][1:]
        years: list[str] = []
        values: list[float] = []
        for header, cell in zip(headers, cells):
            if "Q" in header.upper():
                continue
            value = _parse_number(cell)
            if value is None:
                continue
            years.append(header)
            values.append(value)
        if years and values:
            return years, values
    return None


def _load_financial_series(data_pack_path: Path) -> FinancialSeries | None:
    if not data_pack_path.exists():
        return None
    md_text = data_pack_path.read_text(encoding="utf-8")
    revenue = _find_financial_row(md_text, "营业收入")
    net_profit = _find_financial_row(md_text, "归母净利润")
    fcf = _find_financial_row(md_text, "自由现金流")
    roe = _find_financial_row(md_text, "ROE (%)")
    operating_cash_flow = _find_financial_row(md_text, "经营现金流")
    gross_margin = _find_financial_row(md_text, "毛利率 (%)")
    receivables = _find_financial_row(md_text, "应收账款")
    inventory = _find_financial_row(md_text, "存货")
    if not (revenue and net_profit and fcf and roe):
        return None
    common_years = [year for year in revenue[0] if year in net_profit[0] and year in fcf[0] and year in roe[0]]
    common_years = sorted(common_years)[-5:]
    if len(common_years) < 3:
        return None

    def values_for(row: tuple[list[str], list[float]]) -> list[float]:
        lookup = dict(zip(row[0], row[1]))
        return [lookup[year] for year in common_years]

    def optional_values_for(row: tuple[list[str], list[float]] | None) -> list[float]:
        if row is None:
            return []
        lookup = dict(zip(row[0], row[1]))
        if not all(year in lookup for year in common_years):
            return []
        return [lookup[year] for year in common_years]

    return FinancialSeries(
        years=common_years,
        revenue=values_for(revenue),
        net_profit=values_for(net_profit),
        fcf=values_for(fcf),
        roe=values_for(roe),
        operating_cash_flow=optional_values_for(operating_cash_flow),
        gross_margin=optional_values_for(gross_margin),
        receivables=optional_values_for(receivables),
        inventory=optional_values_for(inventory),
    )


def _setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def _write_line_chart(path: Path, years: list[str], series: list[tuple[str, list[float]]], ylabel: str) -> None:
    plt = _setup_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=180)
    for label, values in series:
        ax.plot(years, values, marker="o", linewidth=2, label=label)
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _write_bar_line_chart(
    path: Path,
    years: list[str],
    bars: list[tuple[str, list[float]]],
    lines: list[tuple[str, list[float]]],
    left_ylabel: str,
    right_ylabel: str,
) -> None:
    plt = _setup_matplotlib()
    fig, ax = plt.subplots(figsize=(7.2, 4.0), dpi=180)
    x_positions = list(range(len(years)))
    bar_width = 0.34 if len(bars) > 1 else 0.48
    offset_start = -bar_width * (len(bars) - 1) / 2
    for index, (label, values) in enumerate(bars):
        offsets = [x + offset_start + index * bar_width for x in x_positions]
        ax.bar(offsets, values, width=bar_width, alpha=0.72, label=label)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(years)
    ax.set_ylabel(left_ylabel)
    ax.grid(True, axis="y", alpha=0.25)

    ax_right = ax.twinx()
    for label, values in lines:
        ax_right.plot(x_positions, values, marker="o", linewidth=2, label=label)
    ax_right.set_ylabel(right_ylabel)

    handles, labels = ax.get_legend_handles_labels()
    right_handles, right_labels = ax_right.get_legend_handles_labels()
    ax.legend(handles + right_handles, labels + right_labels, frameon=False, loc="best")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _values_in_yi_yuan(values_in_million_yuan: list[float]) -> list[float]:
    return [value / 100 for value in values_in_million_yuan]


def _year_over_year(values: list[float]) -> list[float]:
    rates: list[float] = []
    for index, value in enumerate(values):
        if index == 0 or values[index - 1] == 0:
            rates.append(0.0)
        else:
            rates.append((value / values[index - 1] - 1) * 100)
    return rates


def _trend_word(values: list[float], positive: str, negative: str, mixed: str) -> str:
    if len(values) < 2:
        return mixed
    delta = values[-1] - values[0]
    if delta > 0:
        return positive
    if delta < 0:
        return negative
    return mixed


def _revenue_profit_reading(series: FinancialSeries) -> str:
    revenue = _trend_word(series.revenue, "改善", "回落", "持平")
    profit = _trend_word(series.net_profit, "改善", "回落", "持平")
    if revenue == "改善" and profit == "改善":
        return "营业收入和归母净利润同向改善，说明增长至少阶段性转化为利润。"
    if revenue == "改善" and profit != "改善":
        return "营业收入增长没有同步转化为归母净利润，需检查毛利率、费用率或周期压力。"
    if revenue != "改善" and profit == "改善":
        return "收入没有明显扩张但利润改善，需判断来自效率提升、价格修复还是一次性因素。"
    return "收入和利润同步承压，商业质量判断需要重点结合周期位置和现金流韧性。"


def _cash_return_reading(series: FinancialSeries) -> str:
    fcf = _trend_word(series.fcf, "改善", "回落", "持平")
    roe = _trend_word(series.roe, "改善", "回落", "持平")
    if fcf == "改善" and roe == "改善":
        return "自由现金流和 ROE 同步改善，利润质量有现金和回报率支撑。"
    if fcf != "改善" and roe == "改善":
        return "ROE 改善但自由现金流没有同步改善，需要警惕利润含金量或资本开支压力。"
    if fcf == "改善" and roe != "改善":
        return "自由现金流改善但 ROE 未同步修复，说明现金安全垫好于股东回报弹性。"
    return "自由现金流和 ROE 同步承压，需要下调对商业质量稳定性的信心或提高周期折价。"


def _company_chart_profile(md_text: str) -> str:
    structured = "\n".join(
        line
        for line in md_text.splitlines()
        if "capital_intensity" in line or "cyclicality" in line
    )
    if "capital-hungry" in structured or "强周期" in structured:
        return "cycle"
    if "capital-light" in structured or "弱周期" in structured:
        return "light_asset"

    profile_text = re.sub(r"(?:不是|并非|非)重资产\S*", "", md_text)
    profile_text = re.sub(r"(?:不是|并非|非|不像|而非)强周期\S*", "", profile_text)
    profile_text = re.sub(r"(?:不是|并非|非|不像|而非)轻资产\S*", "", profile_text)
    has_cycle_profile = "强周期" in profile_text or "capital-hungry" in profile_text or "重资产" in profile_text
    has_light_profile = "轻资产" in profile_text or "capital-light" in profile_text
    if has_cycle_profile:
        return "cycle"
    if has_light_profile:
        return "light_asset"
    if "应收" in profile_text and "存货" in profile_text:
        return "light_asset"
    return "base"


def _cash_conversion_reading(series: FinancialSeries) -> str:
    if not series.operating_cash_flow:
        return "经营现金流数据不足，重点观察应收和存货是否继续占用利润。"
    ratio = series.operating_cash_flow[-1] / series.net_profit[-1] if series.net_profit[-1] else 0
    if ratio >= 1:
        return "经营现金流覆盖净利润，利润含金量暂有现金支撑。"
    return "经营现金流未完全覆盖净利润，需要观察应收和存货是否继续占用现金。"


def _cycle_quality_reading(series: FinancialSeries) -> str:
    if not series.gross_margin:
        return "毛利率数据不足，周期质量仍需结合 ROE 和行业景气验证。"
    roe = _trend_word(series.roe, "改善", "回落", "持平")
    margin = _trend_word(series.gross_margin, "改善", "回落", "持平")
    if roe == "改善" and margin == "改善":
        return "ROE 与毛利率同步修复，周期底部后的经营质量出现改善信号。"
    if roe != "改善" and margin == "改善":
        return "毛利率改善尚未完全转化为 ROE 修复，需要继续观察资本效率。"
    return "ROE 或毛利率仍承压，周期公司商业质量不宜只看低估值。"


def _create_wechat_financial_charts(report_path: Path, output_dir: Path) -> list[str]:
    series = _load_financial_series(report_path.parent / "data_pack_market.md")
    if series is None:
        return []
    charts_dir = output_dir / "charts"
    revenue_profit = charts_dir / "revenue_profit.png"
    fcf_roe = charts_dir / "fcf_roe.png"
    revenue_profit_title = "收入利润趋势：收入增长是否同步转化为利润"
    fcf_roe_title = "现金回报趋势：利润是否有现金和 ROE 支撑"
    _write_bar_line_chart(
        revenue_profit,
        series.years,
        [("营业收入", _values_in_yi_yuan(series.revenue)), ("归母净利润", _values_in_yi_yuan(series.net_profit))],
        [("营业收入同比", _year_over_year(series.revenue)), ("归母净利润同比", _year_over_year(series.net_profit))],
        "亿元",
        "%",
    )
    _write_bar_line_chart(
        fcf_roe,
        series.years,
        [("自由现金流", _values_in_yi_yuan(series.fcf))],
        [("ROE", series.roe)],
        "亿元",
        "%",
    )
    chart_lines = [
        "## 关键财务趋势图",
        "",
        f"### {revenue_profit_title}",
        "",
        f"![{revenue_profit_title}](charts/revenue_profit.png)",
        "",
        f"**读图结论**：{_revenue_profit_reading(series)}",
        "",
        f"### {fcf_roe_title}",
        "",
        f"![{fcf_roe_title}](charts/fcf_roe.png)",
        "",
        f"**读图结论**：{_cash_return_reading(series)}",
        "",
    ]
    profile = _company_chart_profile(report_path.read_text(encoding="utf-8"))
    if profile == "cycle" and series.gross_margin:
        cycle_quality = charts_dir / "cycle_quality.png"
        cycle_title = "周期质量趋势：ROE 与毛利率是否同步修复"
        _write_line_chart(cycle_quality, series.years, [("ROE", series.roe), ("毛利率", series.gross_margin)], "%")
        chart_lines.extend([
            f"### {cycle_title}",
            "",
            f"![{cycle_title}](charts/cycle_quality.png)",
            "",
            f"**读图结论**：{_cycle_quality_reading(series)}",
            "",
        ])
    elif profile == "light_asset" and series.operating_cash_flow:
        cash_conversion = charts_dir / "cash_conversion.png"
        conversion_title = "现金转化趋势：利润是否被应收和存货占用"
        extra_series = [("经营现金流", series.operating_cash_flow), ("归母净利润", series.net_profit)]
        if series.receivables:
            extra_series.append(("应收账款", series.receivables))
        if series.inventory:
            extra_series.append(("存货", series.inventory))
        _write_line_chart(
            cash_conversion,
            series.years,
            [(label, _values_in_yi_yuan(values)) for label, values in extra_series],
            "亿元",
        )
        chart_lines.extend([
            f"### {conversion_title}",
            "",
            f"![{conversion_title}](charts/cash_conversion.png)",
            "",
            f"**读图结论**：{_cash_conversion_reading(series)}",
            "",
        ])
    chart_lines.append("图表基于上市公司年报和 Tushare 数据生成，用于辅助阅读商业质量变化。")
    return chart_lines


def _insert_chart_section(md_text: str, chart_lines: list[str]) -> str:
    if not chart_lines or "## 关键财务趋势图" in md_text:
        return md_text
    marker = re.search(r"^##\s+Executive Summary / 执行摘要\s*$", md_text, flags=re.MULTILINE)
    if marker:
        insert_at = marker.start()
        return md_text[:insert_at] + "\n".join(chart_lines) + "\n\n---\n\n" + md_text[insert_at:]
    return md_text.rstrip() + "\n\n" + "\n".join(chart_lines) + "\n"


def create_polished_qualitative_markdown(report_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    polished_path = output_dir / f"{report_path.stem}.polished.md"
    polished = polish_qualitative_markdown(report_path.read_text(encoding="utf-8"))
    polished = _insert_chart_section(polished, _create_wechat_financial_charts(report_path, output_dir))
    polished_path.write_text(polished, encoding="utf-8")
    return polished_path


def preview_html_path_for(report_path: Path, output_dir: Path) -> Path:
    stem = report_path.stem
    if stem.endswith(".polished"):
        stem = stem.removesuffix(".polished")
    return output_dir / f"{stem}.preview.html"


def build_wxgzh_command(
    report_path: Path,
    *,
    output_dir: Path,
    account: str | None,
    author: str | None,
    digest: str | None,
    theme: str | None,
    cover: Path | None,
    no_cover: bool,
) -> list[str]:
    command = ["npx", "-y", "@lyhue1991/wxgzh", str(report_path), "--output-dir", str(output_dir)]
    if account:
        command.extend(["--account", account])
    if author:
        command.extend(["--author", author])
    if digest:
        command.extend(["--digest", digest])
    if theme:
        command.extend(["--theme", theme])
    if cover is not None:
        command.extend(["--cover", str(cover)])
    if no_cover:
        command.append("--no-cover")
    return command


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create draft-box entries from finished Turtle Investment Framework reports"
    )
    parser.add_argument("path", type=Path, help="Output directory or Markdown report file")
    parser.add_argument("--type", choices=REPORT_TYPES, help="Report type when path is an output directory")
    parser.add_argument("--file", type=Path, help="Explicit Markdown report file")
    parser.add_argument("--account", help="wxgzh account name")
    parser.add_argument("--author", help="Article author passed to wxgzh")
    parser.add_argument("--digest", help="Article digest passed to wxgzh")
    parser.add_argument("--theme", help="wxgzh theme name")
    parser.add_argument("--cover", type=Path, help="Cover image path passed to wxgzh")
    parser.add_argument("--no-cover", action="store_true", help="Pass --no-cover to wxgzh")
    parser.add_argument("--output-dir", type=Path, help="wxgzh output directory")
    parser.add_argument("--skip-validation", action="store_true", help="Skip finished-report validation")
    parser.add_argument(
        "--qualitative-polish",
        action="store_true",
        help="Create a presentation-polished qualitative Markdown copy under .wxgzh before drafting",
    )
    parser.add_argument(
        "--preview-html",
        action="store_true",
        help="Generate a local standalone HTML preview for qualitative polish mode",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the npx command without running it")
    parser.add_argument("--yes", action="store_true", help="Required for real draft creation")
    args, unknown = parser.parse_known_args(argv)
    credential_args = [arg for arg in unknown if arg.split("=", 1)[0].lower() in CREDENTIAL_LIKE_ARGS]
    if credential_args:
        raise SystemExit(
            "Credential-like arguments are not supported: "
            + ", ".join(credential_args)
            + ". Configure wxgzh credentials outside this project."
        )
    if unknown:
        parser.error("unrecognized arguments: " + " ".join(unknown))
    return args


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    report_path = discover_report(args.path, args.type, args.file)
    inferred_report_type = infer_report_type(report_path)
    report_type = args.type or inferred_report_type
    if args.qualitative_polish and inferred_report_type != "qualitative":
        raise SystemExit("--qualitative-polish only supports qualitative reports")
    qualitative_polish = args.qualitative_polish or report_type == "qualitative"

    if not args.skip_validation:
        validate_before_draft(report_path, report_type)

    output_dir = args.output_dir or report_path.parent / ".wxgzh"
    draft_report_path = report_path
    digest = args.digest
    if args.preview_html and not qualitative_polish:
        raise SystemExit("--preview-html requires --qualitative-polish")
    if qualitative_polish:
        draft_report_path = create_polished_qualitative_markdown(report_path, output_dir)
        if digest is None:
            digest = auto_digest_from_qualitative(report_path.read_text(encoding="utf-8"))
    preview_path = None
    if args.preview_html:
        preview_path = preview_html_path_for(draft_report_path, output_dir)
        render_report_html(draft_report_path, preview_path, standalone=True)
    if qualitative_polish:
        readiness_issues = validate_wechat_draft_readiness(draft_report_path, preview_path)
        if readiness_issues:
            raise SystemExit("WeChat draft readiness failed: " + ", ".join(readiness_issues))

    command = build_wxgzh_command(
        draft_report_path,
        output_dir=output_dir,
        account=args.account,
        author=args.author,
        digest=digest,
        theme=args.theme,
        cover=args.cover,
        no_cover=args.no_cover,
    )
    if args.dry_run:
        print(shlex.join(command))
        return
    if not args.yes:
        raise SystemExit("--yes is required for real draft creation")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
