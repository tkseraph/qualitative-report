"""Load and render the canonical finished-report contract."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


CONTRACT_PATH = Path(__file__).resolve().parent.parent / "shared" / "report_contract.json"
SUPPORTED_SCHEMA_VERSION = 1


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
    header = " | ".join(card["header"])
    return "\n".join([
        "【唯一报告契约（机器校验与生成共用）】",
        f"- 首屏卡固定表头：| {header} |；必含：{'、'.join(card['required_rows'])}。",
        f"- D6 固定小标题：{d6['decision_heading']}；必含：{'、'.join(d6['required_topics'])}。",
        f"- 强周期/重资产公司至少 {charts['minimum_modules']} 个可渲染图表，且每个必须显式 chart_ready；"
        f"chart_type 仅允许：{', '.join(charts['allowed_types'])}。",
        f"- 未来观察优先级固定为：{' / '.join(future['priority_tiers'])}；"
        f"表格必含：{'、'.join(future['required_columns'])}。",
        f"- 机器字段：{'、'.join(contract['machine_fields'])}。",
        f"- 契约源：{CONTRACT_PATH}",
    ])
