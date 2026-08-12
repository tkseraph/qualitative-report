#!/usr/bin/env python3
"""Validate finished report Markdown files against product schemas."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from qualitative_quality import rating_errors, structured_param
    from report_contract import report_contract
    from report_schema import REPORT_SCHEMAS, ReportSchema, SchemaRequirement
except ModuleNotFoundError:  # package import: scripts.validate_reports
    from scripts.qualitative_quality import rating_errors, structured_param
    from scripts.report_contract import report_contract
    from scripts.report_schema import REPORT_SCHEMAS, ReportSchema, SchemaRequirement


QUALITATIVE_CONTRACT = report_contract("qualitative")


@dataclass(frozen=True)
class ValidationResult:
    report_type: str
    path: str
    ok: bool
    missing: list[str]
    messages: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _has_any_keyword(normalized_text: str, requirement: SchemaRequirement) -> bool:
    return any(keyword.lower() in normalized_text for keyword in requirement.any_keywords)


def _has_requirement(md_text: str, normalized_text: str, requirement: SchemaRequirement) -> bool:
    if requirement.name == "six dimensions":
        return all(
            re.search(rf"^##\s+(?:维度{number}|D{index}\b)", md_text, flags=re.MULTILINE | re.IGNORECASE)
            for index, number in enumerate(("一", "二", "三", "四", "五", "六"), start=1)
        )
    return _has_any_keyword(normalized_text, requirement)


def _missing_requirements(md_text: str, schema: ReportSchema) -> list[SchemaRequirement]:
    normalized = _normalize(md_text)
    return [
        requirement
        for requirement in schema.requirements
        if not _has_requirement(md_text, normalized, requirement)
    ]


def _template_placeholder_messages(md_text: str) -> list[str]:
    messages: list[str] = []
    brace_matches = sorted(
        {
            match.group(0)
            for match in re.finditer(r"\{([^{}\n]{1,40})\}", md_text)
            if not re.search(r"[:,]", match.group(1))
        }
    )
    if brace_matches:
        messages.append(
            "Unreplaced template placeholder(s): " + ", ".join(brace_matches[:5])
        )
    todo_matches = sorted(set(re.findall(r"\b(?:TODO|TBD)\b", md_text, re.IGNORECASE)))
    if todo_matches:
        messages.append(
            "Unreplaced template placeholder(s): " + ", ".join(todo_matches)
        )
    return messages


def _section_body(md_text: str, heading_keywords: tuple[str, ...]) -> str:
    lines = md_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") and any(keyword in stripped for keyword in heading_keywords):
            start = index + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("#"):
            break
        body.append(line)
    return "\n".join(body).strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _heading_or_line_text(
    md_text: str,
    heading_keywords: tuple[str, ...],
    line_keywords: tuple[str, ...],
) -> str:
    section_text = _section_body(md_text, heading_keywords)
    matching_lines = [
        line
        for line in md_text.splitlines()
        if any(keyword in line for keyword in line_keywords)
    ]
    return "\n".join([section_text, *matching_lines]).strip()


def _core_contradiction_refutation_section_exists(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("核心矛盾", "反证条件"))
    return bool(section_text) and _contains_any(
        section_text,
        ("反证", "推翻判断", "重评", "下调", "降级"),
    )


def _first_screen_text(md_text: str) -> str:
    lines = md_text.splitlines()
    headings_seen = 0
    collected: list[str] = []
    for line in lines:
        if line.startswith("## "):
            headings_seen += 1
            if headings_seen > 4:
                break
        collected.append(line)
    return "\n".join(collected)


def _heading_start_index(md_text: str, heading_keywords: tuple[str, ...]) -> int | None:
    for index, line in enumerate(md_text.splitlines()):
        stripped = line.strip()
        if stripped.startswith("#") and any(keyword in stripped for keyword in heading_keywords):
            return index
    return None


def _h2_section_body(md_text: str, heading_keywords: tuple[str, ...]) -> str:
    lines = md_text.splitlines()
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and any(keyword in stripped for keyword in heading_keywords):
            start = index + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        if line.strip().startswith("## "):
            break
        body.append(line)
    return "\n".join(body).strip()


def _section_contains_all(md_text: str, heading_keywords: tuple[str, ...], required_terms: tuple[str, ...]) -> bool:
    section_text = _h2_section_body(md_text, heading_keywords)
    return bool(section_text) and all(term in section_text for term in required_terms)


def _markdown_table_header_exists(md_text: str, header: tuple[str, ...]) -> bool:
    expected = "|" + "|".join(f" {cell} " for cell in header) + "|"
    compact_expected = re.sub(r"\s+", "", expected)
    return any(re.sub(r"\s+", "", line.strip()) == compact_expected for line in md_text.splitlines())


def _is_markdown_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _has_reader_facing_table_intro(text: str) -> bool:
    meaningful_lines = [
        line.strip().lstrip("#").strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("|")
    ]
    return bool(meaningful_lines)


def _has_instruction_like_table_prose(md_text: str) -> bool:
    patterns = (
        r"这张表\s*(?:同时)?(?:用于)?回答",
        r"下表\s*(?:同时)?(?:用于)?回答",
        r"这张表用于",
        r"下表用于",
        r"用一张\s*[^\n。；;]{0,20}表回答",
        r"表格用于回答",
        r"(?:这张|下表|本表)[^\n。；;]{0,20}表[^\n。；;]{0,12}(?:结论|含义|说明)",
        r"表格(?:用于|回答|说明)",
        r"避免只证明",
        r"不要只写优势",
        r"不要只证明",
        r"不检查伪优势",
    )
    return any(re.search(pattern, md_text) for pattern in patterns)


def _table_context_issues(md_text: str) -> bool:
    lines = md_text.splitlines()
    index = 0
    while index < len(lines) - 1:
        if lines[index].strip().startswith("|") and _is_markdown_table_separator(lines[index + 1]):
            header = re.sub(r"\s+", "", lines[index])
            if (
                "|项目|结论|" in header
                or "|指标|结论|" in header
                or "|参数|" in header
                or "|优先级|观察变量|" in header
            ):
                index += 1
                continue
            previous_text = "\n".join(lines[max(0, index - 3):index])
            next_index = index + 2
            while next_index < len(lines) and lines[next_index].strip().startswith("|"):
                next_index += 1
            following_text = "\n".join(lines[next_index:min(len(lines), next_index + 3)])
            has_intro = _has_reader_facing_table_intro(previous_text)
            has_meaning = _contains_any(following_text, ("结论", "含义", "说明", "因此", "意味着", "投资", "复盘状态", "兑现状态"))
            if not has_intro or not has_meaning:
                return True
            index = next_index
            continue
        index += 1
    return False


def _dimension_sections(md_text: str) -> list[str]:
    sections: list[str] = []
    for index, number in enumerate(("一", "二", "三", "四", "五", "六"), start=1):
        body = _h2_section_body(md_text, (f"维度{number}", f"D{index}"))
        if body:
            sections.append(body)
    return sections


def _dimension_section_map(md_text: str) -> dict[int, str]:
    sections: dict[int, str] = {}
    for index, number in enumerate(("一", "二", "三", "四", "五", "六"), start=1):
        body = _h2_section_body(md_text, (f"维度{number}", f"D{index}"))
        if body:
            sections[index] = body
    return sections


def _markdown_table_count(section_text: str) -> int:
    lines = section_text.splitlines()
    return sum(
        1
        for index in range(len(lines) - 1)
        if lines[index].strip().startswith("|") and _is_markdown_table_separator(lines[index + 1])
    )


def _markdown_table_blocks(section_text: str) -> list[str]:
    lines = section_text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines) - 1:
        if lines[index].strip().startswith("|") and _is_markdown_table_separator(lines[index + 1]):
            start = index
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                index += 1
            blocks.append("\n".join(lines[start:index]))
            continue
        index += 1
    return blocks


def _parse_markdown_table(table_text: str) -> tuple[list[str], list[list[str]]]:
    rows = []
    for line in table_text.strip().splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or _is_markdown_table_separator(stripped):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _has_markdown_table_with_terms(section_text: str, required_terms: tuple[str, ...]) -> bool:
    return any(all(term in block for term in required_terms) for block in _markdown_table_blocks(section_text))


def _has_merged_business_amount_cell(md_text: str) -> bool:
    product_terms = r"(?:\d+(?:\.\d+)?级水泥|熟料|骨料|机制砂|商混|商品混凝土)"
    pattern = rf"\|[^|\n]*{product_terms}[^|\n]{{0,16}}约\s*\d+(?:\.\d+)?\s*(?:亿元|万元)"
    return bool(re.search(pattern, md_text))


def _has_dimension_evidence_tables(sections: dict[int, str]) -> bool:
    return len(sections) >= 6 and all(_markdown_table_count(section) >= 1 for section in sections.values())


_COMPANY_SPECIFIC_EVIDENCE_TERMS = (
    "ROE",
    "Capex",
    "D&A",
    "OCF",
    "FCF",
    "毛利率",
    "费用率",
    "研发",
    "渠道",
    "库存",
    "海外",
    "平台",
    "港口",
    "吞吐",
    "单箱",
    "集疏运",
    "吨价",
    "吨成本",
    "吨毛利",
    "固定资产",
    "折旧",
    "自由现金流",
    "子公司",
    "投资收益",
    "非经常性损益",
    "质押",
)


def _has_company_specific_evidence(section_text: str) -> bool:
    if not section_text:
        return False
    text_without_dimension_labels = re.sub(r"\bD[1-6]\b", "", section_text)
    return bool(re.search(r"\d", text_without_dimension_labels)) or _contains_any(
        section_text,
        _COMPANY_SPECIFIC_EVIDENCE_TERMS,
    )


def _has_company_specific_evidence_each_dimension(sections: dict[int, str]) -> bool:
    return len(sections) >= 6 and all(_has_company_specific_evidence(section) for section in sections.values())


def _has_dimension_summary_contract(section_text: str) -> bool:
    summary = _section_body(section_text, ("本章小结",))
    return bool(summary) and _contains_any(summary, ("本章结论",)) and _contains_any(
        summary,
        ("最重要证据", "核心证据", "关键证据"),
    ) and _has_dimension_summary_risk_trigger(section_text)


def _has_dimension_summary_risk_trigger(section_text: str) -> bool:
    summary = _section_body(section_text, ("本章小结",))
    return bool(summary) and _contains_any(summary, ("观察风险", "重评触发", "风险触发", "反证条件"))


def _has_d2_peer_comparison(section_text: str) -> bool:
    if not section_text:
        return False
    unavailable_terms = ("同业数据不可得", "无可比上市公司", "缺少可比公司", "可比公司数据不可得")
    if _contains_any(section_text, unavailable_terms):
        return True
    peer_terms = ("同业", "同行", "竞争对手", "可比公司", "竞品", "对标")
    return any(
        _contains_any(block, peer_terms) and _named_peer_count_in_block(block) >= 2
        for block in _markdown_table_blocks(section_text)
    )


def _has_d1_business_formula(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("公司赚钱公式",)) and _has_markdown_table_with_terms(
        section_text,
        ("收入来源", "利润驱动", "资本占用", "现金转化", "关键反证"),
    )


def _has_d1_working_capital_cash_bridge(section_text: str) -> bool:
    """Require cash attribution that separates assets from operating financing."""
    if not section_text:
        return False
    has_cash_bridge = _contains_any(section_text, ("OCF", "经营现金流", "现金流")) and all(
        _contains_any(section_text, alternatives)
        for alternatives in (
            ("应收",),
            ("存货", "库存"),
            ("应付", "供应商信用"),
            ("合同负债", "预收"),
        )
    )
    separates_financing = _contains_any(
        section_text,
        ("客户融资", "经营融资", "提供融资", "融资来源", "资金来源", "预收融资"),
    ) and _contains_any(
        section_text,
        ("占用", "耗用现金", "消耗现金"),
    )
    has_attribution = _contains_any(
        section_text,
        ("现金桥", "桥接", "解释了经营现金流", "解释OCF", "现金影响", "现金贡献"),
    )
    return has_cash_bridge and separates_financing and has_attribution


def _requires_d1_working_capital_cash_bridge(md_text: str, section_text: str) -> bool:
    collection_mode = structured_param(md_text, "collection_mode")
    return collection_mode in {"先款后货", "垫资回收", "先货后款"} or (
        _contains_any(section_text, ("项目", "定制", "工程"))
        and _contains_any(section_text, ("存货", "合同负债", "预收"))
    )


def _has_d2_moat_falsification(section_text: str) -> bool:
    if not section_text or "护城河证伪表" not in section_text:
        return False
    falsification_blocks = [
        block for block in _markdown_table_blocks(section_text)
        if "支持护城河" in block
        and "削弱护城河" in block
        and re.search(r"可持续\s*KPI", block)
    ]
    if not falsification_blocks or not _contains_any(
        section_text,
        ("同业", "同行", "竞争对手", "可比公司", "竞品", "对标"),
    ):
        return False
    # A table is evidence storage, not falsification analysis.  Require prose
    # that compares at least two hypotheses and states the retained boundary.
    for block in falsification_blocks:
        start = section_text.find(block)
        context = section_text[max(0, start - 900):start + len(block) + 1400]
        competing_hypotheses = _contains_any(
            context,
            ("假设", "如果", "若", "只来自", "不能解释", "反例"),
        )
        verdict = _contains_any(
            context,
            ("没有通过验证", "被否定", "不成立", "保留结论", "证伪后", "仍成立"),
        )
        rating_boundary = _contains_any(
            context,
            ("不足以上调", "不支持上调", "不支持强", "限制了", "评级维持", "综合护城河"),
        )
        if competing_hypotheses and verdict and rating_boundary:
            return True
    return False


def _has_d2_competing_hypothesis_synthesis(section_text: str) -> bool:
    if not section_text:
        return False
    hypothesis_markers = re.findall(
        r"(?:第一种|第二种|假说一|假说二|假设一|假设二|解释一|解释二)[^\n。；;]{0,100}(?:假说|假设|解释)?",
        section_text,
    )
    if len(hypothesis_markers) < 2:
        return False
    has_evidence_verdict = _contains_any(
        section_text,
        ("支持第一种", "支持第二种", "保留", "被否定", "不成立", "不足以排除", "不能排除"),
    )
    has_peer_counterexample = bool(re.search(
        r"(?:同业|同行|竞品|可比公司)[^\n。；;]{0,100}(?:反例|不支持|接近|更高|更低|边界|不能证明)",
        section_text,
    ))
    has_rating_effect = _contains_any(
        section_text,
        ("评级维持", "评级上调", "评级上修", "评级下调", "评级影响", "护城河评为", "综合评级"),
    )
    return has_evidence_verdict and has_peer_counterexample and has_rating_effect


def _has_d2_moat_interrogation_chain(section_text: str) -> bool:
    if not section_text:
        return False
    for block in _markdown_table_blocks(section_text):
        headers, rows = _parse_markdown_table(block)
        if not headers or not rows:
            continue
        header_text = "|".join(headers)
        if not all(
            _contains_any(header_text, alternatives)
            for alternatives in (
                ("步骤", "审讯环节"),
                ("审讯问题", "问题"),
                ("事实与作用机制", "事实与机制", "作用机制"),
                ("当前结论", "当前判断", "结论"),
                ("失效信号", "失败信号", "反证信号"),
            )
        ):
            continue
        if len(rows) != 6 or any(len(row) < 5 for row in rows):
            continue
        step_numbers: list[int] = []
        for row in rows:
            match = re.match(r"\s*([1-6])(?:\.|、|\s)", row[0])
            if not match:
                break
            step_numbers.append(int(match.group(1)))
        if step_numbers != [1, 2, 3, 4, 5, 6]:
            continue
        if not all(len(row[1].strip()) >= 8 and len(row[2].strip()) >= 12 and len(row[4].strip()) >= 6 for row in rows):
            continue
        block_end = section_text.find(block) + len(block)
        synthesis = section_text[block_end:block_end + 1000]
        if _contains_any(synthesis, ("边界", "不是", "并非", "限制", "保护", "上限", "下限")) and _contains_any(
            synthesis,
            ("投资含义", "因此", "这意味着", "结论"),
        ):
            return True
    return False


def _has_d3_cycle_sensitivity_threshold(section_text: str) -> bool:
    return bool(section_text) and _has_markdown_table_with_terms(
        section_text,
        ("当前阶段", "财务敏感性", "预警阈值"),
    ) and _contains_any(section_text, ("周期", "外部变量", "行业景气")) and _contains_any(
        section_text,
        ("重评", "下调", "预警"),
    )


def _has_d3_cycle_roe_repair_chain(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("需求周期", "需求", "行业需求")) and _contains_any(
        section_text,
        ("价格/成本", "价格", "成本", "毛利率", "单位利润"),
    ) and _contains_any(
        section_text,
        ("ROE 修复空间", "ROE修复空间", "ROE 修复", "ROE修复"),
    ) and _contains_any(
        section_text,
        ("评级上修", "上修", "维持观察", "下调评级"),
    ) and _contains_any(
        section_text,
        ("反证阈值", "预警阈值", "重评", "下调"),
    )


def _has_d3_cycle_data_evidence(section_text: str) -> bool:
    if not section_text:
        return False
    required_groups = (
        ("需求", "销量", "吞吐"),
        ("价格", "吨价", "单箱收益", "ASP"),
        ("成本", "吨成本", "单位成本"),
        ("毛利率", "吨毛利", "单位毛利"),
        ("ROE",),
        ("FCF", "自由现金流"),
    )
    for block in _markdown_table_blocks(section_text):
        if len(re.findall(r"20\d{2}", block)) < 3:
            continue
        if all(_contains_any(block, alternatives) for alternatives in required_groups):
            return True
    return False


def _has_order_cycle_transmission(section_text: str) -> bool:
    if not section_text or not _contains_any(section_text, ("当前阶段", "当前处于", "当前无法", "当前判断")):
        return False
    stages = (
        ("客户资本开支", "客户扩产", "下游需求", "客户需求"),
        ("设备订单", "订单"),
        ("制造", "生产", "交付"),
        ("验收",),
        ("收入", "收入确认"),
        ("回款", "现金", "经营现金流"),
    )
    has_all_stages = all(_contains_any(section_text, alternatives) for alternatives in stages)
    has_causal_language = _contains_any(
        section_text,
        ("→", "传导", "先改变", "再改变", "最终通过", "进入收入", "转化为现金"),
    )
    return has_all_stages and has_causal_language


def _has_d5_management_narrative_audit(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("管理层叙事审计", "管理层核心叙事")) and _has_markdown_table_with_terms(
        section_text,
        ("管理层说法", "财务验证", "是否兑现", "沉默信息", "重评动作"),
    )


def _has_d5_silence_check(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("风险措辞变化", "风险表述变化")) and _contains_any(
        section_text,
        ("未解释清楚的问题", "沉默信息", "管理层没有解释", "管理层未解释"),
    )


def _has_d5_history_guidance_strategy_review(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("历史指引", "上一年目标", "去年目标", "管理层目标")) and _contains_any(
        section_text,
        ("实际兑现", "当年实际", "是否兑现", "兑现"),
    ) and _contains_any(section_text, ("新战略", "新业务", "新项目", "经营计划"))


def _has_d4_governance_chain(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("治理红旗", "审计意见", "关联交易")) and _contains_any(
        section_text,
        ("资本配置", "分红", "回购", "Capex", "并购", "投资回报"),
    ) and _contains_any(section_text, ("承诺兑现", "言行一致", "目标", "兑现"))


def _has_d4_management_control_check(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("管理层", "控制权", "实控人", "实际控制人", "控股股东"))


def _has_d4_capital_allocation_review(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("资本配置复盘", "资本配置的多年复盘")) and _has_markdown_table_with_terms(
        section_text,
        ("动作", "金额", "管理层理由", "后续结果", "质量评价"),
    )


def _has_d4_governance_red_flag_audit(section_text: str) -> bool:
    if not section_text:
        return False
    required_groups = (
        ("审计意见",),
        ("审计师变更", "审计机构变更", "会计师变更"),
        ("处罚", "监管处罚", "立案"),
        ("资金占用", "非经营占用"),
        ("关联交易",),
        ("担保", "或有负债"),
        ("质押", "股权质押"),
        ("管理层稳定性", "核心管理层", "频繁离任"),
    )
    for block in _markdown_table_blocks(section_text):
        if _contains_any(block, ("红旗", "排雷", "异常阈值", "重评动作")) and all(_contains_any(block, alternatives) for alternatives in required_groups):
            return True
    return False


def _has_d5_guidance_delivery_review(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("历史目标 vs 实际兑现", "历史目标VS实际兑现", "历史目标的多年兑现状态")) and _has_markdown_table_with_terms(
        section_text,
        ("年份", "管理层目标", "实际结果", "偏差", "投资含义"),
    )


def _has_d5_mda_interrogation_table(section_text: str) -> bool:
    if not section_text:
        return False
    return _contains_any(section_text, ("MD&A 审讯", "MD&A审讯", "叙事审讯")) and any(
        all(term in block for term in ("管理层原始说法", "财务验证", "实际兑现", "风险措辞变化", "沉默信息", "下一年复核指标"))
        for block in _markdown_table_blocks(section_text)
    )


def _has_d6_trigger_table(section_text: str) -> bool:
    heading = QUALITATIVE_CONTRACT["d6"]["decision_heading"]
    return (
        bool(section_text)
        and heading in section_text
        and _contains_any(section_text, ("触发条件", "是否展开", "是否触发"))
        and _markdown_table_count(section_text) >= 1
    )



def _has_d6_subsidiary_investment_sotp(section_text: str) -> bool:
    return bool(section_text) and sum(
        1
        for alternatives in (
            ("子公司", "母公司", "合并"),
            ("投资收益", "非经常性损益"),
            ("SOTP", "分部估值", "控股折价"),
        )
        if _contains_any(section_text, alternatives)
    ) >= 2


def _has_d6_threshold_calculation_basis(section_text: str) -> bool:
    return bool(section_text) and _contains_any(section_text, ("阈值", "占比", "比例", "%", "超过", "低于", "高于")) and _contains_any(
        section_text,
        ("计算依据", "计算口径", "母合差异", "母公司", "合并", "净利润", "利润占比", "投资收益占比", "非经常性损益占比"),
    )


def _has_d6_sotp_mode_contract(md_text: str, section_text: str) -> bool:
    d6 = QUALITATIVE_CONTRACT["d6"]
    values = {
        field: structured_param(md_text, field)
        for field in d6["required_decision_fields"]
    }
    if any(not value for value in values.values()):
        return False
    if values["sotp_mode"] not in d6["modes"]:
        return False
    if values["sotp_data_readiness"] not in {
        "sufficient", "partial", "insufficient", "not_applicable"
    }:
        return False
    mode_readable = {
        "not_applicable": ("不适用", "not_applicable"),
        "diagnostic": ("诊断", "diagnostic"),
        "listed_asset_bridge": ("上市资产", "价值桥", "listed_asset_bridge"),
        "full": ("完整 SOTP", "完整SOTP", "full"),
    }[values["sotp_mode"]]
    return _contains_any(section_text, mode_readable) and _contains_any(
        section_text,
        ("重复计价", "重复计算", "重复加总", "不可加回", "不能再加"),
    ) and _contains_any(section_text, ("升级", "触发", "启动"))


def _has_d6_economic_separability(md_text: str, section_text: str) -> bool:
    value = structured_param(md_text, "sotp_economic_separability")
    allowed = QUALITATIVE_CONTRACT["analysis_quality"]["sotp_economic_separability_values"]
    if value not in allowed:
        return False
    mode = structured_param(md_text, "sotp_mode")
    if mode == "not_applicable":
        return value == "not_applicable" and _contains_any(section_text, ("不适用", "经济可分拆"))
    if mode == "full" and value != "demonstrated":
        return False
    topic_groups = (
        ("客户",),
        ("产品", "技术", "工艺"),
        ("管理", "共享资源", "资源分摊"),
        ("现金流",),
        ("净债务", "债务"),
        ("资本开支", "Capex"),
        ("内部交易", "内部抵销", "关联交易"),
    )
    return _contains_any(section_text, ("经济可分拆", "经济独立", "独立分拆")) and sum(
        1 for alternatives in topic_groups if _contains_any(section_text, alternatives)
    ) >= 6


def _has_roe_history_coverage(md_text: str) -> bool:
    years_text = structured_param(md_text, "roe_history_years")
    available_avg = structured_param(md_text, "roe_available_years_avg")
    five_year_avg = structured_param(md_text, "roe_5y_avg")
    match = re.search(r"\d+", years_text)
    if not match or not available_avg:
        return False
    years = int(match.group(0))
    null_values = {"null", "none", "n/a", "na", "不适用", "—", "-"}
    if years < 5:
        return five_year_avg.strip().lower() in null_values
    return bool(five_year_avg) and five_year_avg.strip().lower() not in null_values


def _uses_current_analysis_contract(md_text: str, quality_contract: str) -> bool:
    if quality_contract == "current":
        return True
    if quality_contract == "legacy":
        return False
    return bool(structured_param(md_text, "analysis_contract_version"))


def _uses_readable_money_units(md_text: str) -> bool:
    return "百万元" not in md_text


def _has_qualitative_sample_evidence_modules(md_text: str) -> bool:
    module_terms = (
        ("收入质量拆分", "收入质量分解", "收入结构拆分"),
        ("利润桥", "利润质量分解", "利润增量拆解"),
        ("量价成本拆解", "量价成本", "价格-销量-成本"),
        ("现金转化", "经营现金流/净利润", "自由现金流"),
        ("治理红旗", "治理红旗检查"),
        ("MD&A 叙事 vs 财务证据", "管理层叙事 vs 财务证据", "叙事与财务证据", "叙事验证"),
        ("伪优势过滤", "真优势", "半真优势", "伪优势", "优势过滤"),
    )
    return all(any(term in md_text for term in alternatives) for alternatives in module_terms)


def _has_company_specific_evidence_modules(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("样板证据模块", "证据模块"))
    if not section_text:
        return False
    table_rows = [line for line in section_text.splitlines() if line.strip().startswith("|")]
    evidence_rows = [line for line in table_rows if not _is_markdown_table_separator(line) and "模块" not in line]
    company_specific_rows = [line for line in evidence_rows if re.search(r"\d", line)]
    return len(company_specific_rows) >= 2


def _has_adaptive_research_plan(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("自适应研究计划",))
    if not section_text:
        return False
    has_plan_schema = _has_markdown_table_with_terms(section_text, ("项目", "判断", "证据路径", "反证重点"))
    has_research_logic = _contains_any(section_text, ("公司类型",)) and _contains_any(
        section_text,
        ("核心质量问题", "关键因果链", "核心因果链"),
    )
    if not has_plan_schema or not has_research_logic:
        return False
    normalized_section = re.sub(r"\s+", "", section_text)
    light_asset_terms = ("轻资产", "软件", "平台", "互联网")
    conch_cement_terms = ("吨价", "吨成本", "熟料", "矿山", "水泥价格战", "碳价")
    if _contains_any(section_text, light_asset_terms) and _contains_any(section_text, conch_cement_terms):
        return False
    return "证据必须服务核心判断" in section_text or "不是机械照搬" in section_text or "不机械照搬" in section_text or "不是固定复制" in section_text or "按公司逻辑" in section_text or bool(re.search(r"证据路径[^\n]{0,120}(收入|利润|现金|ROE|FCF|费用率|研发|海外|渠道|吨价|吨成本|Capex|D&A|投资收益|非经常性损益)", normalized_section))


def _has_cross_validation_research_layers(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("交叉验证与深度分析", "交叉验证", "深度分析"))
    if not section_text:
        return False
    return _contains_any(section_text, ("数字与叙事的匹配", "叙事 vs 财务", "叙事与财务")) and _contains_any(
        section_text,
        ("核心矛盾",),
    ) and _contains_any(
        section_text,
        ("被忽视信号", "忽视信号", "沉默信息"),
    ) and _contains_any(
        section_text,
        ("非经营项", "投资收益", "资产减值", "公允价值", "营业外"),
    ) and _contains_any(
        section_text,
        ("口径差异", "口径"),
    )


def _has_limitations_data_warnings(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("报告局限与数据警示", "数据警示", "报告局限"))
    if not section_text:
        return False
    return _contains_any(section_text, ("数据口径冲突", "口径差异", "口径冲突")) and _contains_any(
        section_text,
        ("同业数据缺口", "同业数据", "竞品数据", "可比公司数据"),
    ) and _contains_any(
        section_text,
        ("披露不足", "未披露", "披露限制"),
    ) and _contains_any(
        section_text,
        ("后续复核", "复核动作", "继续跟踪"),
    )


def _has_strong_cycle_unit_economics(md_text: str, sections: dict[int, str]) -> bool:
    strong_cycle_terms = ("强周期", "周期公司", "周期属性")
    if not _contains_any(md_text, strong_cycle_terms):
        return True
    search_text = "\n".join((sections.get(1, ""), _h2_section_body(md_text, ("自适应研究计划",)), _h2_section_body(md_text, ("公司类型化证据模块",))))
    return _contains_any(search_text, ("单位经济模型", "单位经济")) and _contains_any(
        search_text,
        ("销量", "销售量", "出货量", "吞吐量"),
    ) and _contains_any(
        search_text,
        ("吨价", "隐含吨价", "单价", "ASP"),
    ) and _contains_any(
        search_text,
        ("吨成本", "单位成本"),
    ) and _contains_any(
        search_text,
        ("吨毛利", "单位毛利"),
    )


def _has_strong_cycle_industry_evidence_depth(md_text: str, sections: dict[int, str]) -> bool:
    if not _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")):
        return True
    search_text = _h2_section_body(md_text, ("公司类型化证据模块", "类型化证据模块"))
    if not search_text:
        return False
    return _contains_any(search_text, ("产业坐标", "行业坐标", "行业地图", "区域", "客户结构")) and _contains_any(
        search_text,
        ("同业/区域坐标", "同业", "同行", "竞品", "可比公司", "对标"),
    ) and _contains_any(
        search_text,
        ("单位经济模型", "吨价", "ASP", "单价"),
    ) and _contains_any(
        search_text,
        ("利润桥", "现金质量", "FCF", "自由现金流"),
    ) and _contains_any(
        search_text,
        ("反证阈值", "预警阈值", "重评", "下调", "降级"),
    )


def _profit_bridge_text(md_text: str) -> str:
    search_sections = (_h2_section_body(md_text, ("维度一", "D1")), _h2_section_body(md_text, ("样板证据模块", "证据模块")))
    profit_rows: list[str] = []
    detail_terms = ("营业收入", "营业成本", "毛利", "销售费用", "管理费用", "研发费用", "财务费用", "资产减值", "信用减值", "投资收益", "非经常性损益", "核心经营利润")
    for section in search_sections:
        for block in _markdown_table_blocks(section):
            if not _contains_any(block, ("利润桥", "利润质量", "利润增量", *detail_terms)):
                continue
            rows = [line for line in block.splitlines()[2:] if line.strip().startswith("|")]
            if sum(1 for term in detail_terms if term in block) >= 3:
                profit_rows.extend(rows)
        if profit_rows:
            break
    return "\n".join(profit_rows)


def _has_profit_bridge_component_depth(md_text: str) -> bool:
    if not _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")):
        return True
    search_text = _profit_bridge_text(md_text)
    return sum(
        1
        for alternatives in (
            ("毛利", "收入成本", "营业成本"),
            ("销售费用", "管理费用", "研发费用", "期间费用"),
            ("资产减值", "信用减值", "减值", "坏账"),
            ("投资收益", "处置收益", "公允价值", "营业外", "非经营项", "非经常性损益"),
        )
        if _contains_any(search_text, alternatives)
    ) >= 3


def _has_profit_bridge_expense_detail(md_text: str) -> bool:
    if not _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")):
        return True
    search_text = _profit_bridge_text(md_text)
    return sum(1 for term in ("销售费用", "管理费用", "研发费用", "财务费用") if term in search_text) >= 2


def _has_profit_bridge_core_operating_recast(md_text: str) -> bool:
    if not _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")):
        return True
    search_text = "\n".join((_profit_bridge_text(md_text), _h2_section_body(md_text, ("样板证据模块", "证据模块")), _h2_section_body(md_text, ("维度一", "D1"))))
    return _contains_any(search_text, ("核心经营利润", "可持续利润")) and _contains_any(
        search_text,
        ("剔除", "重算", "还原", "调整后"),
    ) and _contains_any(
        search_text,
        ("非经常性损益", "一次性因素", "非经营项", "投资收益"),
    ) and _contains_any(
        search_text,
        ("支撑当前评级", "支撑评级", "评级仍成立", "需要下调"),
    )


def _has_profit_bridge_recast_calculation_basis(md_text: str) -> bool:
    if not _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")):
        return True
    search_text = "\n".join((_profit_bridge_text(md_text), _h2_section_body(md_text, ("样板证据模块", "证据模块")), _h2_section_body(md_text, ("维度一", "D1"))))
    return _contains_any(search_text, ("核心经营利润重算", "核心经营利润")) and _contains_any(
        search_text,
        ("报表归母净利", "报表利润", "归母净利", "净利润"),
    ) and "投资收益" in search_text and _contains_any(
        search_text,
        ("非经常性损益", "一次性因素"),
    ) and _contains_any(
        search_text,
        ("计算口径", "计算依据"),
    )


def _peer_comparison_search_text(md_text: str, sections: dict[int, str]) -> str:
    return "\n".join((sections.get(2, ""), _h2_section_body(md_text, ("公司类型化证据模块", "类型化证据模块"))))


def _has_named_peer_or_unavailable_explanation(md_text: str, sections: dict[int, str]) -> bool:
    search_text = _peer_comparison_search_text(md_text, sections)
    if _contains_any(search_text, ("同业数据不可得", "可比数据不可得", "无可比上市公司", "缺少可比公司", "可比公司数据缺口")):
        return True
    peer_blocks = [block for block in _markdown_table_blocks(search_text) if _contains_any(block, ("同业", "同行", "竞品", "可比", "对标", "公司"))]
    generic_names = {"公司", "同行公司", "可比公司", "同业公司", "竞品公司", "目标公司"}
    concrete_names: set[str] = set()
    for block in peer_blocks:
        for line in block.splitlines()[2:]:
            if not line.strip().startswith("|"):
                continue
            first_cell = line.strip().strip("|").split("|")[0].strip()
            if first_cell in generic_names:
                continue
            if re.search(r"(?:集团|股份|控股|银行|水泥|网络|科技|实业|能源|电力|医药|食品|港口|物流)$", first_cell) or re.fullmatch(r"[一-龥]{2,6}港", first_cell):
                concrete_names.add(first_cell)
    return len(concrete_names) >= 2


def _named_peer_count_in_block(block: str) -> int:
    generic_names = {"公司", "同行公司", "可比公司", "同业公司", "竞品公司", "目标公司"}
    count = 0
    for line in block.splitlines()[2:]:
        if not line.strip().startswith("|"):
            continue
        first_cell = line.strip().strip("|").split("|")[0].strip()
        if first_cell in generic_names:
            continue
        if re.search(r"(?:集团|股份|控股|银行|水泥|网络|科技|实业|能源|电力|医药|食品|港口|物流)$", first_cell) or re.fullmatch(r"[一-龥]{2,6}港", first_cell):
            count += 1
    return count


def _has_peer_comparison_dimensions(md_text: str, sections: dict[int, str]) -> bool:
    search_text = _peer_comparison_search_text(md_text, sections)
    if _contains_any(search_text, ("同业数据不可得", "可比数据不可得", "无可比上市公司", "缺少可比公司", "可比公司数据缺口")):
        return True
    dimension_terms = (
        "ROE",
        "毛利率",
        "净利率",
        "成本",
        "费用率",
        "资产负债率",
        "Capex",
        "D&A",
        "现金流",
        "吨价",
        "吨成本",
        "吨毛利",
        "区域",
        "份额",
        "主业利润占比",
        "投资收益",
    )
    peer_blocks = [block for block in _markdown_table_blocks(search_text) if _contains_any(block, ("同业", "同行", "竞品", "可比", "对标", "公司"))]
    return any(_named_peer_count_in_block(block) >= 2 and sum(1 for term in dimension_terms if term in block) >= 2 for block in peer_blocks)


def _has_holding_network_depth(section_text: str) -> bool:
    if not section_text:
        return False
    trigger_rows = "\n".join(line for line in section_text.splitlines() if line.strip().startswith("|") and not _is_markdown_table_separator(line))
    return _contains_any(trigger_rows, ("控股股东", "实控人", "实际控制人", "控制权")) and _contains_any(
        trigger_rows,
        ("子公司", "主要子公司", "孙公司"),
    ) and _contains_any(
        trigger_rows,
        ("关联平台", "相关上市平台", "关联上市平台", "同系上市平台", "集团平台"),
    )


def _chart_friendly_heading_pattern() -> re.Pattern[str]:
    return re.compile(r"^###\s*(.*(?:关键图表|业务拆分|收入质量|利润桥|吨经济|单位经济|区域毛利|区域结构|资本消耗|现金质量|现金转化|近五年质量趋势|吞吐结构|同业坐标|同业对比|竞争对标|现金|利润|降本).*)$", flags=re.MULTILINE)


def _chart_friendly_section_bodies(md_text: str) -> list[str]:
    bodies: list[str] = []
    for match in _chart_friendly_heading_pattern().finditer(md_text):
        start = match.end()
        next_heading = re.search(r"^#{2,3}\s+", md_text[start:], flags=re.MULTILINE)
        bodies.append(md_text[start:start + next_heading.start()] if next_heading else md_text[start:])
    return bodies


def _chart_ready_section_bodies(md_text: str) -> list[str]:
    bodies: list[str] = []
    for match in re.finditer(r"^chart_ready:\s*true\s*;.*$", md_text, flags=re.MULTILINE):
        start = match.start()
        next_heading = re.search(r"^#{2,3}\s+", md_text[match.end():], flags=re.MULTILINE)
        bodies.append(md_text[start:match.end() + next_heading.start()] if next_heading else md_text[start:])
    return bodies


def _chart_ready_metadata_lines(md_text: str) -> list[str]:
    return re.findall(r"^chart_ready:\s*true\s*;.*$", md_text, flags=re.MULTILINE)


def _is_cycle_or_heavy_asset_report(md_text: str) -> bool:
    capital_intensity = structured_param(md_text, "capital_intensity")
    cyclicality = structured_param(md_text, "cyclicality")
    if capital_intensity or cyclicality:
        return capital_intensity == "capital-hungry" or cyclicality == "强周期"
    return _contains_any(md_text, tuple(QUALITATIVE_CONTRACT["chart_ready"]["conditional_company_types"]))


def _has_chart_ready_metadata_contract(md_text: str) -> bool:
    metadata_lines = _chart_ready_metadata_lines(md_text)
    if len(metadata_lines) < 2:
        return False
    chart_contract = QUALITATIVE_CONTRACT["chart_ready"]
    required_fields = tuple(
        f"{field}:" for field in chart_contract["required_metadata"]
    )
    allowed_types = "|".join(map(re.escape, chart_contract["allowed_types"]))
    return all(
        all(field in line for field in required_fields)
        and re.search(rf"chart_type:\s*(?:{allowed_types})\b", line)
        for line in metadata_lines
    )


def _has_chart_routing_metadata_contract(md_text: str) -> bool:
    if structured_param(md_text, "rating_version") != "2.0":
        return True
    lines = _chart_ready_metadata_lines(md_text)
    if not lines:
        return False
    chart_ids: list[str] = []
    allowed_targets = {"executive_summary", "trend", *(f"dimension_{index}" for index in range(1, 7))}
    for line in lines:
        chart_id_match = re.search(r"(?:^|;)\s*chart_id:\s*([a-z0-9][a-z0-9-]*)", line)
        target_match = re.search(r"(?:^|;)\s*chart_target:\s*([a-z0-9_]+)", line)
        if not chart_id_match or not target_match or target_match.group(1) not in allowed_targets:
            return False
        chart_ids.append(chart_id_match.group(1))
    return len(chart_ids) == len(set(chart_ids))


def _has_current_golden_chart_contract(md_text: str) -> bool:
    expected = int(QUALITATIVE_CONTRACT["html"]["golden_core_chart_count"])
    if len(_chart_ready_metadata_lines(md_text)) != expected:
        return False
    titles = re.findall(
        r"^###\s+图表([一二三四五六七八九十]+)[：:]",
        md_text,
        flags=re.MULTILINE,
    )
    expected_titles = set(list("一二三四五六")[:expected])
    return len(titles) == expected and set(titles) == expected_titles


def _has_sample_level_chart_ready_coverage(md_text: str) -> bool:
    if not _is_cycle_or_heavy_asset_report(md_text):
        return True
    return len(_chart_ready_metadata_lines(md_text)) >= int(
        QUALITATIVE_CONTRACT["chart_ready"]["minimum_modules"]
    )


def _chart_ready_search_text(md_text: str) -> str:
    return "\n".join([*_chart_ready_metadata_lines(md_text), *_chart_ready_section_bodies(md_text)])


def _has_chart_ready_archetype_coverage(md_text: str) -> bool:
    if not _is_cycle_or_heavy_asset_report(md_text):
        return True
    search_text = _chart_ready_search_text(md_text)
    archetypes = (
        ("收入占比", "业务", "区域结构", "业务拆分", "收入质量"),
        ("Capex/D&A", "资本开支与折旧", "折旧摊销", "D&A"),
        ("OCF/净利润", "经营现金流/净利润", "营运资本", "应收账款", "应收"),
        ("ROE", "毛利率", "净利率", "盈利能力", "五年趋势"),
        ("同业坐标", "同业对比", "同行对比", "竞争对标", "可比公司", "效率对比"),
    )
    return all(_contains_any(search_text, alternatives) for alternatives in archetypes)


def _is_clean_chart_numeric_cell(raw: str) -> bool:
    stripped = raw.strip()
    if not stripped:
        return False
    return bool(re.fullmatch(r"-?\d+(?:,\d{3})*(?:\.\d+)?\s*(?:%|亿元|百万元|万元|万箱|箱|万吨|吨|元/吨|元/kg|元/箱|元|倍|x|X)?", stripped))


def _has_chart_ready_numeric_tables(md_text: str) -> bool:
    explanatory_headers = (
        "投资含义",
        "含义",
        "结论",
        "判断",
        "质量判断",
        "评价",
        "证据",
        "解释",
        "说明",
        "来源",
        "口径",
        "变化方向",
    )
    for body in _chart_ready_section_bodies(md_text):
        tables = _markdown_table_blocks(body)
        if not tables:
            return False
        headers, rows = _parse_markdown_table(tables[0])
        if len(headers) < 2 or not rows:
            return False
        if any(any(token in header for token in explanatory_headers) for header in headers[1:]):
            return False
        for row in rows:
            for column_index in range(1, len(headers)):
                raw = row[column_index] if column_index < len(row) else ""
                if not _is_clean_chart_numeric_cell(raw):
                    return False
    return True


def _has_chart_readouts_for_chart_friendly_tables(md_text: str) -> bool:
    for body in _chart_friendly_section_bodies(md_text):
        if "|" in body and "读图结论" not in body:
            return False
    return True


def _has_chart_evidence_investment_meaning(md_text: str) -> bool:
    impact_terms = (
        "投资含义",
        "评级",
        "风险",
        "反证",
        "重评",
        "下调",
        "上修",
        "降级",
        "支撑当前评级",
        "评级仍成立",
    )
    for body in _chart_friendly_section_bodies(md_text):
        if "|" in body and "读图结论" in body and not _contains_any(body, impact_terms):
            return False
    return True


def _has_chart_evidence_density(md_text: str) -> bool:
    if not _is_cycle_or_heavy_asset_report(md_text):
        return True
    count = 0
    has_counted_multi_year = False
    for match in _chart_friendly_heading_pattern().finditer(md_text):
        title = match.group(1)
        start = match.end()
        next_heading = re.search(r"^#{2,3}\s+", md_text[start:], flags=re.MULTILINE)
        body = md_text[start:start + next_heading.start()] if next_heading else md_text[start:]
        if "|" in body and "读图结论" in body:
            count += 1
            has_counted_multi_year = has_counted_multi_year or _contains_any(title + body, ("近五年", "五年趋势", "质量趋势"))
    if not has_counted_multi_year and _has_multi_year_trend_evidence(md_text):
        count += 1
    return count >= 4


def _has_reader_facing_chart_titles(md_text: str) -> bool:
    module_titles = ("单位经济模型", "资本配置复盘表", "收入利润ROE因果链", "利润桥", "现金质量", "同业坐标")
    for match in re.finditer(r"^###\s*(.+)$", md_text, flags=re.MULTILINE):
        title = match.group(1).strip()
        if title.startswith("读图结论：") or title in module_titles:
            return False
    return True


def _has_cross_validation_final_reassessment(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("交叉验证与深度分析", "交叉验证", "深度分析"))
    if not section_text:
        return False
    return _contains_any(section_text, ("综合复判", "最终复判", "最终判断")) and _contains_any(
        section_text,
        ("评级", "商业质量", "护城河"),
    ) and _contains_any(
        section_text,
        ("仍成立", "成立", "需要下调", "下调", "重评", "降级"),
    )


def _has_cross_validation_reassessment_table(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("交叉验证与深度分析", "交叉验证", "深度分析"))
    if not section_text:
        return False
    required_rows = (
        "支持当前评级的证据",
        "削弱当前评级的证据",
        "证据冲突的解释",
        "触发重评的最小变量",
    )
    return any(
        "评级动作" in block and all(row in block for row in required_rows)
        for block in _markdown_table_blocks(section_text)
    )


def _has_future_observation_priority_tiers(md_text: str) -> bool:
    section_text = _h2_section_body(md_text, ("未来观察", "观察变量", "监控KPI"))
    if not section_text:
        return False
    future = QUALITATIVE_CONTRACT["future_observation"]
    return _has_markdown_table_with_terms(
        section_text, tuple(future["required_columns"])
    ) and all(tier in section_text for tier in future["priority_tiers"])


def _has_multi_year_trend_evidence(md_text: str) -> bool:
    if not _is_cycle_or_heavy_asset_report(md_text):
        return True
    section_text = _h2_section_body(md_text, ("近五年", "五年趋势", "趋势证据", "质量趋势"))
    if not section_text:
        section_text = _section_body(md_text, ("近五年", "五年趋势", "趋势证据", "质量趋势"))
    if not section_text:
        return False
    return _has_markdown_table_with_terms(section_text, ("ROE", "FCF")) and _contains_any(
        section_text,
        ("毛利率", "净利率", "Capex/D&A", "资本开支"),
    ) and len(re.findall(r"20\d{2}", section_text)) >= 3


def _has_d4_d5_multi_year_review(sections: dict[int, str]) -> bool:
    d4 = sections.get(4, "")
    d5 = sections.get(5, "")
    if not d4 or not d5:
        return False
    d4_has_years = len(re.findall(r"20\d{2}", d4)) >= 2 or bool(re.search(r"20\d{2}\s*[-—至到]\s*20\d{2}", d4))
    d5_has_years = len(re.findall(r"20\d{2}", d5)) >= 3 or bool(re.search(r"20\d{2}\s*[-—至到]\s*20\d{2}", d5))
    return d4_has_years and d5_has_years and _contains_any(
        d4,
        ("多年复盘", "多年兑现", "复盘状态", "后续结果"),
    ) and _contains_any(
        d5,
        ("多年兑现", "兑现状态", "历史目标", "实际兑现"),
    )


def _has_public_output_internal_artifacts(md_text: str) -> bool:
    patterns = [
        r"/Users/[^\s`，。；;|]+",
        r"/tmp/[^\s`，。；;|]+",
        r"output/[^\s`，。；;|]+",
        r"WebSearch\s*fallback",
        r"acceptance samples?",
        r"\be2e\b",
        r"\bfixture\b",
        r"\bvalidator\b",
        r"\bCM§\d+",
        r"\bDP§[A-Za-z0-9]+",
        r"\bqualitative_(?:evidence|argument_map|content_audit)\.json\b",
    ]
    patterns.extend(QUALITATIVE_CONTRACT["public_output"]["forbidden_patterns"])
    return any(re.search(pattern, md_text, flags=re.IGNORECASE) for pattern in patterns)


def _has_channel_reuse_label_leakage(md_text: str) -> bool:
    patterns = (
        r"微信公众号摘要\s*可复用",
        r"(?:微信|公众号|小红书|朋友圈|推文|文章)(?:摘要|导语|标题|金句|开头|结尾)[^\n。；;]{0,20}(?:可复用|可直接使用|可用)",
        r"可复用一句话",
        r"可作为(?:微信|公众号|推文|文章)(?:摘要|导语|标题|开头|结尾)",
        r"适合(?:微信|公众号|推文|文章)(?:摘要|导语|标题|开头|结尾)",
    )
    return any(re.search(pattern, md_text, flags=re.IGNORECASE) for pattern in patterns)


def _overlong_body_lines(md_text: str, max_chars: int = 180) -> list[tuple[int, str]]:
    overlong: list[tuple[int, str]] = []
    in_code_fence = False
    for line_number, line in enumerate(md_text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            continue
        if (
            in_code_fence
            or not stripped
            or stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith(">")
            or stripped.startswith("chart_ready:")
        ):
            continue
        if len(stripped) > max_chars:
            overlong.append((line_number, stripped))
    return overlong


def _finished_report_quality_issues(md_text: str) -> list[tuple[str, str]]:
    summary = _section_body(md_text, ("Executive Summary", "执行摘要"))
    compact_summary = re.sub(r"[\s。．.、，,；;：:|\-*]+", "", summary)
    if compact_summary in {"", "内容", "待补充", "略", "暂无"}:
        return [(
            "generic_executive_summary",
            "Executive Summary must contain a finished conclusion, not a generic placeholder.",
        )]
    return []


def _content_quality_issues(
    md_text: str,
    report_type: str,
    quality_contract: str = "auto",
) -> list[tuple[str, str]]:
    normalized = _normalize(md_text)
    issues: list[tuple[str, str]] = _finished_report_quality_issues(md_text)
    if report_type == "qualitative":
        for error in rating_errors(md_text):
            issues.append((
                "qualitative_business_quality_rating",
                "Overall business-quality rating is not canonical or is inconsistent: " + error,
            ))
        verdict_text = _heading_or_line_text(
            md_text,
            ("Business Quality Verdict", "商业质量总体评级", "商业质量"),
            ("Business Quality Verdict", "商业质量", "护城河评级"),
        )
        summary_text = _section_body(md_text, ("Executive Summary", "执行摘要")) + "\n" + _section_body(md_text, ("深度总结", "核心投资逻辑"))
        if _contains_any(verdict_text, ("商业质量优秀", "商业质量较强", "护城河评级强", "护城河评级较强")) and _contains_any(summary_text, ("护城河较弱", "无护城河", "商业质量较弱", "质量下滑")):
            issues.append((
                "qualitative_verdict_self_consistency",
                "Business Quality Verdict conflicts with summary language describing weak moat or quality deterioration.",
            ))
        if _has_instruction_like_table_prose(md_text):
            issues.append((
                "qualitative_instruction_like_prose",
                "Finished qualitative reports must use reader-facing transitions, not instruction-like table prose such as 这张表回答 / 下表回答 / 用于回答.",
            ))
        card_contract = QUALITATIVE_CONTRACT["first_screen_card"]
        if not _markdown_table_header_exists(md_text, tuple(card_contract["header"])) or not _section_contains_all(
            md_text,
            ("Business Quality Verdict", "商业质量总体评级", "商业质量"),
            tuple(card_contract["required_rows"]),
        ):
            issues.append((
                "qualitative_first_screen_card_schema",
                "Business Quality Verdict must include a narrow first-screen card with header '| 项目 | 结论 |' and rows for company essence, quality, moat source, max risk, and refutation condition.",
            ))
        if not _contains_any(md_text, ("五个核心发现", "核心发现")):
            issues.append((
                "qualitative_core_findings",
                "Qualitative report must include five core findings or an equivalent core-findings section near the executive summary.",
            ))
        dimension_sections_by_index = _dimension_section_map(md_text)
        dimension_sections = list(dimension_sections_by_index.values())
        if len(dimension_sections) < 6 or any(not _has_dimension_summary_contract(section) for section in dimension_sections):
            issues.append((
                "qualitative_dimension_summaries",
                "D1-D6 qualitative dimensions must each end with a chapter summary containing conclusion, key evidence, and re-evaluation trigger.",
            ))
        if len(dimension_sections) < 6 or any(
            not _contains_any(section, ("反证", "风险", "限制", "异常", "重评触发", "下调")) or not _has_dimension_summary_risk_trigger(section)
            for section in dimension_sections
        ):
            issues.append((
                "qualitative_dimension_counterevidence",
                "Each qualitative dimension must include counterevidence, limitations, abnormal signals, or re-evaluation triggers, not only positive evidence.",
            ))
        if not _has_dimension_evidence_tables(dimension_sections_by_index):
            issues.append((
                "qualitative_dimension_evidence_tables",
                "D1-D6 qualitative dimensions must each include at least one narrow evidence table for WeChat-readable reasoning.",
            ))
        if not _has_company_specific_evidence_each_dimension(dimension_sections_by_index):
            issues.append((
                "qualitative_dimension_company_specific_evidence",
                "Each qualitative dimension must include company-specific numeric evidence, business facts, or peer comparisons rather than only generic framework language.",
            ))
        if not _has_d1_business_formula(dimension_sections_by_index.get(1, "")):
            issues.append((
                "qualitative_d1_business_formula",
                "D1 business-model analysis must include a compact business formula covering revenue source, profit driver, capital occupation, cash conversion, and key refutation.",
            ))
        if not _has_d2_peer_comparison(dimension_sections_by_index.get(2, "")):
            issues.append((
                "qualitative_d2_peer_comparison",
                "D2 moat analysis must include a peer/competitor comparison table or explicitly explain that comparable-company data is unavailable.",
            ))
        if not _has_d2_moat_falsification(dimension_sections_by_index.get(2, "")):
            issues.append((
                "qualitative_d2_moat_falsification",
                "D2 moat analysis must combine the falsification table with competing hypotheses, a rejected/retained verdict, and an explicit rating boundary.",
            ))
        if not _has_d2_moat_interrogation_chain(dimension_sections_by_index.get(2, "")):
            issues.append((
                "qualitative_d2_moat_interrogation_chain",
                "D2 moat analysis needs exactly six continuous interrogation rows with question, company mechanism, current judgment and failure signal, followed by a boundary synthesis.",
            ))
        if not _has_d3_cycle_sensitivity_threshold(dimension_sections_by_index.get(3, "")):
            issues.append((
                "qualitative_d3_cycle_sensitivity_threshold",
                "D3 external-environment analysis must include a cycle / external-variable sensitivity table with current stage, financial sensitivity, warning thresholds, and re-evaluation action language.",
            ))
        if not _has_d3_cycle_roe_repair_chain(dimension_sections_by_index.get(3, "")):
            issues.append((
                "qualitative_d3_cycle_roe_repair_chain",
                "D3 strong-cycle analysis must trace demand cycle into price/cost, ROE repair space, refutation thresholds, and rating upgrade or downgrade action.",
            ))
        if _contains_any(md_text, ("强周期", "重资产", "周期公司", "capital-hungry")) and not _has_d3_cycle_data_evidence(dimension_sections_by_index.get(3, "")):
            issues.append((
                "qualitative_d3_cycle_data_evidence",
                "D3 strong-cycle analysis must use 3-5 years of data to test demand, price, cost, margin, ROE, and FCF on the same timeline.",
            ))
        if not _has_strong_cycle_unit_economics(md_text, dimension_sections_by_index):
            issues.append((
                "qualitative_strong_cycle_unit_economics",
                "Strong-cycle qualitative reports must include a unit-economics model covering volume, implied price or ASP, unit cost, and unit gross profit.",
            ))
        if not _has_strong_cycle_industry_evidence_depth(md_text, dimension_sections_by_index):
            issues.append((
                "qualitative_strong_cycle_industry_evidence_depth",
                "Strong-cycle or heavy-asset qualitative reports must connect industry / regional coordinates, unit economics, profit bridge, cash quality, and refutation thresholds.",
            ))
        if not _has_profit_bridge_component_depth(md_text):
            issues.append((
                "qualitative_profit_bridge_component_depth",
                "Strong-cycle or heavy-asset qualitative reports must decompose the profit bridge into multiple concrete drivers such as gross profit, expenses, impairments, investment income, and non-operating items where relevant.",
            ))
        if not _has_profit_bridge_expense_detail(md_text):
            issues.append((
                "qualitative_profit_bridge_expense_detail",
                "Strong-cycle or heavy-asset profit bridges must split the expense side into at least two concrete items such as selling, G&A, R&D, or finance expenses.",
            ))
        if not _has_profit_bridge_core_operating_recast(md_text):
            issues.append((
                "qualitative_profit_bridge_core_operating_recast",
                "Strong-cycle or heavy-asset profit bridges must recast reported profit into core operating / sustainable profit by excluding investment income, non-recurring items, and one-off factors, then judge whether sustainable profit supports the rating.",
            ))
        if not _has_profit_bridge_recast_calculation_basis(md_text):
            issues.append((
                "qualitative_profit_bridge_recast_calculation_basis",
                "Strong-cycle or heavy-asset profit bridges must include a calculation basis that can be reconciled from table numbers when recasting reported profit into core operating / sustainable profit.",
            ))
        if not _has_named_peer_or_unavailable_explanation(md_text, dimension_sections_by_index):
            issues.append((
                "qualitative_peer_comparison_named_companies",
                "Peer comparison must name comparable companies or explicitly explain that comparable data is unavailable / not comparable.",
            ))
        if not _has_peer_comparison_dimensions(md_text, dimension_sections_by_index):
            issues.append((
                "qualitative_peer_comparison_dimensions",
                "Peer-coordinate tables must compare named peers on concrete dimensions such as margin, ROE, unit economics, leverage, cash flow, or capital intensity.",
            ))
        if not _has_chart_readouts_for_chart_friendly_tables(md_text):
            issues.append((
                "qualitative_chart_readout_required",
                "Chart-friendly qualitative evidence tables must include reader-facing chart titles or 读图结论 rather than neutral table dumps.",
            ))
        if not _has_chart_evidence_investment_meaning(md_text):
            issues.append((
                "qualitative_evidence_investment_meaning",
                "Chart/evidence tables must explain how evidence affects the rating, risk, or refutation threshold, not only list data.",
            ))
        if not _has_chart_evidence_density(md_text):
            issues.append((
                "qualitative_chart_evidence_density",
                "Strong-cycle or heavy-asset reports must include multiple chart-friendly evidence modules, not just one isolated table.",
            ))
        if not _has_sample_level_chart_ready_coverage(md_text):
            issues.append((
                "qualitative_chart_ready_sample_level_coverage",
                "Strong-cycle or heavy-asset reports must include at least five chart_ready core chart modules so HTML output approaches sample-level evidence density.",
            ))
        if not _has_chart_ready_archetype_coverage(md_text):
            issues.append((
                "qualitative_chart_ready_archetype_coverage",
                "Strong-cycle or heavy-asset chart_ready modules must cover business or region structure, capital consumption, cash conversion, profitability trend, and peer or efficiency comparison.",
            ))
        if not _has_reader_facing_chart_titles(md_text):
            issues.append((
                "qualitative_chart_title_reader_facing",
                "Chart headings must be reader-facing conclusion titles; keep 读图结论 as body text rather than a heading prefix.",
            ))
        if not _has_chart_ready_metadata_contract(md_text):
            issues.append((
                "qualitative_chart_ready_metadata",
                "Core chart modules must include chart_ready metadata with chart_type, x_axis, series, and unit_map so HTML rendering does not guess chart intent.",
            ))
        if not _has_chart_routing_metadata_contract(md_text):
            issues.append((
                "qualitative_chart_routing_metadata",
                "Rating v2 reports must give every chart a unique chart_id and an explicit allowed chart_target.",
            ))
        if not _has_chart_ready_numeric_tables(md_text):
            issues.append((
                "qualitative_chart_ready_numeric_table",
                "chart_ready modules must use pure numeric tables; explanatory columns such as evidence, judgment, implication, source, or calculation notes belong before or after the table.",
            ))
        if not _has_multi_year_trend_evidence(md_text):
            issues.append((
                "qualitative_multi_year_trend_evidence",
                "Strong-cycle or heavy-asset qualitative reports must include multi-year trend evidence covering ROE, margin or profitability, FCF, and capital intensity.",
            ))
        if not _has_d4_governance_chain(dimension_sections_by_index.get(4, "")):
            issues.append((
                "qualitative_d4_governance_chain",
                "D4 governance analysis must cover governance red flags, capital allocation, and delivery / consistency checks.",
            ))
        if not _has_d4_management_control_check(dimension_sections_by_index.get(4, "")):
            issues.append((
                "qualitative_d4_management_control_check",
                "D4 governance analysis must explicitly check management or control-right / controlling-shareholder stability.",
            ))
        if not _has_d4_capital_allocation_review(dimension_sections_by_index.get(4, "")):
            issues.append((
                "qualitative_d4_capital_allocation_review",
                "D4 governance analysis must include a capital-allocation review table covering action, amount, management rationale, later result, and quality assessment.",
            ))
        if not _has_d4_governance_red_flag_audit(dimension_sections_by_index.get(4, "")):
            issues.append((
                "qualitative_d4_governance_red_flag_audit",
                "D4 governance analysis must include a red-flag audit covering audit opinion, auditor changes, penalties, fund occupation, related-party transactions, guarantees, pledges, and management stability.",
            ))
        if not _has_d5_silence_check(dimension_sections_by_index.get(5, "")):
            issues.append((
                "qualitative_d5_silence_check",
                "D5 MD&A analysis must check risk wording changes and management silence / unexplained issues, not only repeat management narrative.",
            ))
        if not _has_d5_management_narrative_audit(dimension_sections_by_index.get(5, "")):
            issues.append((
                "qualitative_d5_management_narrative_audit",
                "D5 MD&A analysis must audit management narrative against financial evidence, delivery, silence, and re-evaluation actions.",
            ))
        if not _has_d5_history_guidance_strategy_review(dimension_sections_by_index.get(5, "")):
            issues.append((
                "qualitative_d5_history_guidance_strategy_review",
                "D5 MD&A analysis must review historical guidance, actual delivery, new strategy, financial validation, risk wording changes, and management silence.",
            ))
        if not _has_d5_guidance_delivery_review(dimension_sections_by_index.get(5, "")):
            issues.append((
                "qualitative_d5_guidance_delivery_review",
                "D5 MD&A analysis must include a historical-targets-vs-actual-delivery table covering year, management target, actual result, deviation, and investment implication.",
            ))
        if not _has_d5_mda_interrogation_table(dimension_sections_by_index.get(5, "")):
            issues.append((
                "qualitative_d5_mda_interrogation_table",
                "D5 MD&A analysis must include an interrogation table covering original management claim, financial validation, actual delivery, risk wording changes, silence, and next-year review KPI.",
            ))
        if not _has_d4_d5_multi_year_review(dimension_sections_by_index):
            issues.append((
                "qualitative_d4_d5_multi_year_review",
                "D4 and D5 reviews must include multi-year delivery status, not only current-year facts.",
            ))
        if not _has_d6_trigger_table(dimension_sections_by_index.get(6, "")):
            issues.append((
                "qualitative_d6_trigger_table",
                "D6 holding-structure analysis must include a trigger-condition table covering whether to expand into subsidiaries, investment income, or SOTP.",
            ))
        if not _has_d6_subsidiary_investment_sotp(dimension_sections_by_index.get(6, "")):
            issues.append((
                "qualitative_d6_subsidiary_investment_sotp",
                "D6 holding-structure analysis must judge at least two of subsidiaries / parent-consolidated differences, investment income / non-recurring items, or SOTP necessity.",
            ))
        if not _has_d6_threshold_calculation_basis(dimension_sections_by_index.get(6, "")):
            issues.append((
                "qualitative_d6_threshold_calculation_basis",
                "D6 holding-structure analysis must include trigger thresholds and calculation basis for subsidiaries, investment income, parent-consolidated differences, non-recurring items, or SOTP necessity.",
            ))
        if not _has_d6_sotp_mode_contract(md_text, dimension_sections_by_index.get(6, "")):
            issues.append((
                "qualitative_d6_sotp_mode_contract",
                "D6 must select a structured SOTP mode and state trigger results, data readiness, decision reason, best feasible analysis, double-counting check, and upgrade trigger.",
            ))
        if not _has_holding_network_depth(dimension_sections_by_index.get(6, "")):
            issues.append((
                "qualitative_holding_network_depth",
                "D6 holding-structure analysis must cover the holding network: controlling shareholder, subsidiaries, related platforms, and related listed platforms where applicable.",
            ))
        if not _uses_readable_money_units(md_text):
            issues.append((
                "qualitative_money_unit_readability",
                "Finished qualitative reports should use readable Chinese money units such as 亿元 or 万元, not 百万元.",
            ))
        if _has_merged_business_amount_cell(md_text):
            issues.append((
                "qualitative_readable_amount_columns",
                "Business / product names and revenue amounts must be split into separate table columns, not merged as 产品名约金额.",
            ))
        required_machine_fields = tuple(QUALITATIVE_CONTRACT["machine_fields"])
        if not _contains_any(md_text, ("结构化参数（机器读取 / 附录）", "结构化参数（机器读取/附录）")) or not all(field in md_text for field in required_machine_fields):
            issues.append((
                "qualitative_machine_fields",
                "Structured parameters must be labeled as a machine-readable appendix and include required qualitative machine fields.",
            ))
        if _uses_current_analysis_contract(md_text, quality_contract):
            analysis_quality = QUALITATIVE_CONTRACT["analysis_quality"]
            current_fields = tuple(analysis_quality["current_machine_fields"])
            if structured_param(md_text, "analysis_contract_version") != analysis_quality["version"] or not all(
                structured_param(md_text, field) for field in current_fields
            ):
                issues.append((
                    "qualitative_current_analysis_machine_fields",
                    "Current qualitative quality contract requires analysis_contract_version 2.1, ROE history coverage fields, and SOTP economic separability.",
                ))
            d1_current = dimension_sections_by_index.get(1, "")
            if _requires_d1_working_capital_cash_bridge(md_text, d1_current) and not _has_d1_working_capital_cash_bridge(d1_current):
                issues.append((
                    "qualitative_working_capital_cash_bridge",
                    "Current-contract D1 must reconcile OCF through receivables, inventory, payables, and contract liabilities while separating asset occupation from operating-liability financing.",
                ))
            if not _has_d2_competing_hypothesis_synthesis(dimension_sections_by_index.get(2, "")):
                issues.append((
                    "qualitative_competing_moat_hypotheses",
                    "Current-contract D2 must compare at least two falsifiable moat hypotheses, use a peer counterexample, and state the rating effect.",
                ))
            if "订单周期" in structured_param(md_text, "cyclicality") and not _has_order_cycle_transmission(
                dimension_sections_by_index.get(3, "")
            ):
                issues.append((
                    "qualitative_order_cycle_transmission",
                    "Order-cycle reports must trace customer demand/capex through order, delivery, acceptance, revenue, and cash, and identify the current stage.",
                ))
            if not _has_d6_economic_separability(md_text, dimension_sections_by_index.get(6, "")):
                issues.append((
                    "qualitative_sotp_economic_separability",
                    "Current-contract D6 must test economic separability across customers, technology, shared resources, cash flow, debt, capex, and internal transactions before choosing SOTP depth.",
                ))
            if not _has_roe_history_coverage(md_text):
                issues.append((
                    "qualitative_roe_history_coverage",
                    "Current-contract ROE fields must distinguish available-history average from a true five-year average; fewer than five annual observations require roe_5y_avg: null.",
                ))
            if not _has_current_golden_chart_contract(md_text):
                issues.append((
                    "qualitative_current_core_chart_contract",
                    "Current-contract HTML qualitative reports must preserve exactly six numbered core charts (图表一 through 图表六) with explicit chart_ready routing.",
                ))
        source_index = _heading_start_index(md_text, ("数据来源",))
        disclaimer_index = _heading_start_index(md_text, ("免责声明",))
        parameter_index = _heading_start_index(md_text, ("结构化参数",))
        if disclaimer_index is None:
            disclaimer_index = _heading_start_index(md_text, ("数据来源与免责声明",))
        if source_index is None or disclaimer_index is None or parameter_index is None or not (source_index <= disclaimer_index < parameter_index):
            issues.append((
                "qualitative_parameter_appendix_order",
                "Structured parameters must appear after data sources and disclaimer so machine-readable fields do not crowd out the human-readable conclusion.",
            ))
        if not _core_contradiction_refutation_section_exists(md_text):
            issues.append((
                "core_contradiction_refutation",
                "Qualitative report must include a core contradiction / refutation section that states what would downgrade the judgment.",
            ))
        if not _has_qualitative_sample_evidence_modules(md_text):
            issues.append((
                "qualitative_sample_evidence_modules",
                "Qualitative report must include sample-level evidence modules: revenue quality split, profit bridge, price-volume-cost, cash conversion, governance red flags, MD&A narrative vs financial evidence, and pseudo-advantage filter.",
            ))
        if not _has_company_specific_evidence_modules(md_text):
            issues.append((
                "qualitative_company_specific_evidence_modules",
                "Qualitative evidence modules must include at least two company-specific numeric or factual evidence rows, not only generic framework labels.",
            ))
        if not _has_adaptive_research_plan(md_text):
            issues.append((
                "qualitative_adaptive_research_plan",
                "Qualitative report must include an adaptive research plan that identifies company type, core quality question, evidence path, and refutation focus without mechanically copying a sample company's sub-sections.",
            ))
        if not _has_cross_validation_research_layers(md_text):
            issues.append((
                "qualitative_cross_validation_research_layers",
                "Qualitative report must include sample-level cross-validation research layers covering narrative-vs-numbers matching, core contradictions, overlooked signals, non-operating items, and accounting-scope differences.",
            ))
        if not _has_cross_validation_final_reassessment(md_text):
            issues.append((
                "qualitative_cross_validation_final_reassessment",
                "Cross-validation analysis must end with an integrated reassessment explaining why the current rating still holds or should be downgraded.",
            ))
        if not _has_cross_validation_reassessment_table(md_text):
            issues.append((
                "qualitative_cross_validation_reassessment_table",
                "Cross-validation analysis must include a rating reassessment table with support, pressure, conflict, trigger, and rating-action rows so HTML can render semantic reassessment cards.",
            ))
        if not _has_limitations_data_warnings(md_text):
            issues.append((
                "qualitative_limitations_data_warnings",
                "Qualitative report must include a limitations and data-warning section covering data-scope conflicts, peer-data gaps, disclosure limits, and follow-up review actions.",
            ))
        if _has_public_output_internal_artifacts(md_text):
            issues.append((
                "qualitative_public_output_cleanliness",
                "Public qualitative reports must not expose source tags, internal evidence IDs, local paths, prompts, validators, fixtures, or workflow-boundary prose.",
            ))
        if _has_channel_reuse_label_leakage(md_text):
            issues.append((
                "qualitative_channel_reuse_leakage",
                "Public qualitative reports must not include channel reuse labels such as 微信公众号摘要可复用一句话; keep only reader-facing article prose.",
            ))
        if _overlong_body_lines(md_text):
            issues.append((
                "qualitative_readability_long_lines",
                "Qualitative report body lines must stay concise for WeChat readability; split long prose into short paragraphs or bullets.",
            ))
        future_observation = _section_body(md_text, ("未来观察", "观察变量", "监控KPI"))
        has_current_evidence_language = _contains_any(
            future_observation,
            ("当前值", "本地证据", "当前值 / 本地证据", "当前证据"),
        )
        has_threshold_language = _contains_any(future_observation, ("预警阈值", "警戒线"))
        has_action_language = _contains_any(future_observation, ("触发后的重评动作", "重评动作", "重评"))
        if not future_observation or not has_current_evidence_language or not has_threshold_language or not has_action_language:
            issues.append((
                "future_observation_thresholds",
                "Future observation variables must include current evidence, warning thresholds, and re-evaluation actions.",
            ))
        if not _has_future_observation_priority_tiers(md_text):
            issues.append((
                "future_observation_priority_tiers",
                "Future observation variables must include priority tiers such as P0/P1/P2 so the monitoring framework is actionable.",
            ))
        if _table_context_issues(md_text):
            issues.append((
                "qualitative_table_context",
                "Qualitative tables must use reader-facing transition or conclusion prose before the table and explain the investment meaning after the table.",
            ))
        first_screen = _first_screen_text(md_text)
        has_advantage = _contains_any(first_screen, ("优势", "护城河", "壁垒", "竞争力", "质量较强", "商业质量"))
        has_risk = _contains_any(first_screen, ("风险", "约束", "压力", "下行"))
        if not has_advantage or not has_risk:
            issues.append((
                "qualitative_first_screen_balance",
                "Qualitative first-screen sections must state both the core advantage/moat and the main risk or constraint.",
            ))
    if report_type == "turtle":
        strategy_text = _heading_or_line_text(
            md_text,
            ("Strategy Verdict", "策略结论"),
            ("Strategy Verdict", "仓位建议", "行动建议", "一句话结论"),
        )
        caution_text = _section_body(md_text, ("行动建议", "仓位建议", "Executive Summary")) + "\n" + md_text
        has_buy_verdict = bool(re.search(r"(?:^|[：:\s/])BUY(?:\s|/|，|。|$)|(?:建议|结论|仓位建议)(?:为)?买入", strategy_text, re.IGNORECASE))
        has_wait_guidance = _contains_any(caution_text, ("WAIT", "wait", "不建仓", "安全边际不足", "低于门槛"))
        if has_buy_verdict and has_wait_guidance:
            issues.append((
                "turtle_verdict_self_consistency",
                "Strategy Verdict gives BUY / 买入 while the report also gives WAIT / no-position or insufficient-margin guidance.",
            ))
    if report_type == "valuation":
        verdict_text = _heading_or_line_text(
            md_text,
            ("Valuation Verdict", "估值总体判断", "估值判断"),
            ("Valuation Verdict", "估值判断", "估值总体判断"),
        )
        conclusion_text = _section_body(md_text, ("估值结论", "Valuation Conclusion", "Executive Summary", "执行摘要")) + "\n" + md_text
        has_positive_verdict = bool(re.search(r"(?:估值判断|Valuation Verdict|估值总体判断)[^\n]{0,30}(?:低估|BUY|建议买入)", verdict_text, re.IGNORECASE))
        has_negative_margin = _contains_any(conclusion_text, ("高估", "不便宜", "负安全边际", "安全边际不足", "缺乏安全边际"))
        if has_positive_verdict and has_negative_margin:
            issues.append((
                "valuation_verdict_self_consistency",
                "Valuation Verdict gives undervalued / buy language while the report conclusion says valuation is expensive or lacks safety margin.",
            ))
    if report_type == "valuation" and re.search(r"(?:原始|raw|结果|为|:|：)\s*DCF[^\n]{0,20}[-－]\s*\d|DCF\s*(?:为|:|：)\s*[-－]\s*\d", md_text, re.IGNORECASE):
        has_diagnostic = "方法适配性诊断" in md_text
        has_demotion = any(term in md_text for term in ("降权", "降级", "权重降至", "权重为 0", "权重为0"))
        has_no_domination = any(term in md_text for term in ("不得机械主导", "不机械主导", "不应主导", "不能机械主导"))
        if not has_diagnostic or not has_demotion or not has_no_domination:
            issues.append((
                "negative_dcf_demotion",
                "Report mentions negative DCF but does not clearly demote it as a method-fit diagnostic that must not mechanically dominate valuation.",
            ))
    if report_type == "turtle" and re.search(r"(?:AA|GG|穿透回报率)\s*(?:为|=|:|：)?\s*(?:负值|[-－]\s*\d)", md_text, re.IGNORECASE):
        has_diagnostic = "诊断值" in md_text
        has_wait = any(term in normalized for term in ("wait", "不建仓", "等待", "观察"))
        verdict_text = "\n".join(
            line for line in md_text.splitlines()
            if any(term in line for term in ("Strategy Verdict", "仓位建议", "行动建议", "一句话结论"))
        )
        verdict_normalized = _normalize(verdict_text)
        has_buy_verdict = any(term in verdict_normalized for term in ("buy", "买入"))
        if not has_diagnostic or has_buy_verdict or not has_wait:
            issues.append((
                "negative_turtle_return",
                "Report mentions negative AA/GG or penetrating return but does not clearly treat it as diagnostic with WAIT / no-position guidance.",
            ))
    return issues


def validate_markdown(
    md_text: str,
    report_type: str,
    path: str = "<memory>",
    quality_contract: str = "auto",
) -> ValidationResult:
    schema = REPORT_SCHEMAS.get(report_type)
    if schema is None:
        known = ", ".join(sorted(REPORT_SCHEMAS))
        return ValidationResult(
            report_type=report_type,
            path=path,
            ok=False,
            missing=[report_type],
            messages=[f"Unknown report type: {report_type}. Expected one of: {known}"],
        )

    missing_requirements = _missing_requirements(md_text, schema)
    placeholder_messages = _template_placeholder_messages(md_text)
    content_issues = _content_quality_issues(md_text, report_type, quality_contract)
    messages = [
        f"Missing {requirement.name}: {requirement.description} "
        f"(expected one of: {', '.join(requirement.any_keywords)})"
        for requirement in missing_requirements
    ] + placeholder_messages + [message for _, message in content_issues]
    missing = [requirement.name for requirement in missing_requirements]
    if placeholder_messages:
        missing.append("template_placeholder")
    missing.extend(name for name, _ in content_issues)
    return ValidationResult(
        report_type=report_type,
        path=path,
        ok=not missing,
        missing=missing,
        messages=messages,
    )


def validate_file(
    path: Path,
    report_type: str,
    quality_contract: str = "auto",
) -> ValidationResult:
    if not path.exists():
        return ValidationResult(
            report_type=report_type,
            path=str(path),
            ok=False,
            missing=["file"],
            messages=[f"Missing file: {path}"],
        )
    return validate_markdown(
        path.read_text(encoding="utf-8"),
        report_type,
        str(path),
        quality_contract,
    )


def _find_matches(output_dir: Path, pattern: str) -> list[Path]:
    return sorted(output_dir.glob(pattern))


def _report_prefix(path: Path, report_type: str) -> str:
    suffix = f"_{report_type}_report.md"
    return path.name.removesuffix(suffix)


def _company_identity(md_text: str) -> str | None:
    first_heading = next(
        (line.strip() for line in md_text.splitlines() if line.strip().startswith("# ")),
        "",
    )
    if not first_heading:
        return None
    heading = first_heading.removeprefix("# ").strip()
    heading = re.sub(r"^(龟龟投资策略|估值分析报告|分析报告)[：:·\s-]*", "", heading).strip()
    if "：" in heading:
        heading = heading.rsplit("：", 1)[1].strip()
    if ":" in heading:
        heading = heading.rsplit(":", 1)[1].strip()
    for separator in ("（", "(", "·", "—", "-"):
        if separator in heading:
            heading = heading.split(separator, 1)[0].strip()
    return heading or None


def _normalize_company_identity(identity: str) -> str:
    normalized = re.sub(r"[\s·—\-（）()：:]", "", identity)
    for suffix in ("集团股份有限公司", "股份有限公司", "集团有限公司", "有限公司", "集团"):
        normalized = normalized.removesuffix(suffix)
    return normalized


def _stock_codes(md_text: str) -> set[str]:
    return {
        f"{match.group(1)}.{match.group(2).upper()}"
        for match in re.finditer(r"\b(\d{6})[._](SH|SZ|BJ)\b", md_text, re.IGNORECASE)
    }


def _validate_content_identity(selected_files: dict[str, Path]) -> ValidationResult | None:
    texts = {
        report_type: path.read_text(encoding="utf-8")
        for report_type, path in selected_files.items()
    }
    codes = {report_type: _stock_codes(text) for report_type, text in texts.items()}
    known_codes = [next(iter(values)) for values in codes.values() if len(values) == 1]
    if len(known_codes) == len(selected_files) and len(set(known_codes)) == 1:
        return None

    identities = {
        report_type: _company_identity(text)
        for report_type, text in texts.items()
    }
    known_identities = {identity for identity in identities.values() if identity}
    normalized_identities = {
        _normalize_company_identity(identity)
        for identity in known_identities
        if _normalize_company_identity(identity)
    }
    if len(normalized_identities) <= 1:
        return None
    return ValidationResult(
        report_type="directory",
        path=str(next(iter(selected_files.values())).parent),
        ok=False,
        missing=["identity_mismatch"],
        messages=[
            "Reports must describe the same company identity: "
            + ", ".join(
                f"{key}={value or '<unknown>'}"
                for key, value in sorted(identities.items())
            )
        ],
    )


def validate_output_dir(
    output_dir: Path,
    quality_contract: str = "auto",
) -> list[ValidationResult]:
    report_matches = {
        "qualitative": _find_matches(output_dir, "*_qualitative_report.md"),
        "turtle": _find_matches(output_dir, "*_turtle_report.md"),
        "valuation": _find_matches(output_dir, "*_valuation_report.md"),
    }
    results: list[ValidationResult] = []
    selected_files: dict[str, Path] = {}
    for report_type, matches in report_matches.items():
        if not matches:
            expected = output_dir / f"*_{report_type}_report.md"
            results.append(
                ValidationResult(
                    report_type=report_type,
                    path=str(expected),
                    ok=False,
                    missing=["file"],
                    messages=[f"Missing {report_type} report matching {expected}"],
                )
            )
        elif len(matches) > 1:
            results.append(
                ValidationResult(
                    report_type=report_type,
                    path=str(output_dir),
                    ok=False,
                    missing=["duplicate_files"],
                    messages=[
                        f"Multiple {report_type} reports found; keep exactly one: "
                        + ", ".join(str(path) for path in matches)
                    ],
                )
            )
        else:
            selected_files[report_type] = matches[0]
            results.append(validate_file(matches[0], report_type, quality_contract))

    if len(selected_files) == len(REPORT_SCHEMAS):
        prefixes = {
            report_type: _report_prefix(path, report_type)
            for report_type, path in selected_files.items()
        }
        if len(set(prefixes.values())) > 1:
            results.append(
                ValidationResult(
                    report_type="directory",
                    path=str(output_dir),
                    ok=False,
                    missing=["prefix_mismatch"],
                    messages=[
                        "Reports must share the same code_market prefix: "
                        + ", ".join(f"{key}={value}" for key, value in sorted(prefixes.items()))
                    ],
                )
            )
        identity_result = _validate_content_identity(selected_files)
        if identity_result is not None:
            results.append(identity_result)
    return results


def _print_result(result: ValidationResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.report_type}: {result.path}")
    for message in result.messages:
        print(f"  - {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate finished A-share report outputs")
    parser.add_argument("path", help="Markdown report file or output directory")
    parser.add_argument(
        "--type",
        choices=sorted(REPORT_SCHEMAS),
        help="Report type when validating a single Markdown file",
    )
    parser.add_argument(
        "--quality-contract",
        choices=("auto", "current", "legacy"),
        default="auto",
        help="Qualitative quality-contract level; current enforces the latest generation rules",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"Path not found: {path}")
    if path.is_dir():
        results = validate_output_dir(path, args.quality_contract)
    else:
        if args.type is None:
            raise SystemExit("--type is required when validating a single Markdown file")
        results = [validate_file(path, args.type, args.quality_contract)]

    for result in results:
        _print_result(result)

    if not all(result.ok for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
