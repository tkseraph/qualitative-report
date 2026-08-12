"""Load and render the canonical finished-report contract."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


CONTRACT_PATH = Path(__file__).resolve().parent.parent / "shared" / "report_contract.json"
SUPPORTED_SCHEMA_VERSION = 2


@lru_cache(maxsize=1)
def load_report_contract() -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise RuntimeError(
            "Unsupported report contract schema version: "
            f"{contract.get('schema_version')!r}"
        )
    reports = contract.get("reports")
    if not isinstance(reports, dict) or "qualitative" not in reports:
        raise RuntimeError("Report contract is missing reports.qualitative")
    return contract


def report_contract(report_type: str) -> dict:
    reports = load_report_contract()["reports"]
    if report_type not in reports:
        raise KeyError(f"Unknown report type: {report_type}")
    return reports[report_type]


def render_qualitative_prompt_contract() -> str:
    """Render strict values for prompts from the same contract as validation."""
    contract = report_contract("qualitative")
    card = contract["first_screen_card"]
    d6 = contract["d6"]
    charts = contract["chart_ready"]
    future = contract["future_observation"]
    rating = contract["business_quality_rating"]
    analysis_quality = contract["analysis_quality"]
    header = " | ".join(card["header"])
    rating_values = "；".join(
        f"{grade} / {item['label']}"
        for grade, item in rating["grades"].items()
    )
    return "\n".join([
        "【唯一报告契约（机器校验与生成共用）】",
        f"- 首屏卡固定表头：| {header} |；必含：{'、'.join(card['required_rows'])}。",
        f"- D6 固定小标题：{d6['decision_heading']}；必含：{'、'.join(d6['required_topics'])}。",
        f"- 总体商业质量评级固定为：{rating_values}；"
        f"展望仅允许：{' / '.join(rating['outlooks'])}；护城河评级必须与总体评级分开。",
        f"- SOTP 模式仅允许：{', '.join(d6['modes'])}；无论选择何种模式都必须给出触发结果、"
        "数据完备度、决策原因、当前最优可行分析、重复计价检查和升级触发条件。",
        f"- 强周期/重资产公司至少 {charts['minimum_modules']} 个可渲染图表，且每个必须显式 chart_ready；"
        f"chart_type 仅允许：{', '.join(charts['allowed_types'])}。",
        f"- 每个核心图表必须提供唯一 chart_id 和显式 chart_target（字段：{', '.join(charts['routing_metadata'])}），避免按标题猜测网页位置。",
        f"- 当前 HTML qualitative 成品固定 {contract['html']['golden_core_chart_count']} 张编号核心图表（图表一至图表六）；定向修订不得增删或改路由。",
        f"- 未来观察优先级固定为：{' / '.join(future['priority_tiers'])}；"
        f"表格必含：{'、'.join(future['required_columns'])}。",
        f"- 机器字段：{'、'.join(contract['machine_fields'])}。",
        f"- 当前分析质量合同：{analysis_quality['version']}；新增机器字段："
        f"{'、'.join(analysis_quality['current_machine_fields'])}。",
        "- 当前质量合同还要求：项目营运资金现金桥、护城河竞争假说、订单周期传导、"
        "SOTP 经济可分拆性与 ROE 历史覆盖检查。",
        f"- 契约源：{CONTRACT_PATH}",
    ])
