"""Finished-report schemas for the A-share three-report product."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from report_contract import report_contract
except ModuleNotFoundError:  # package import: scripts.report_schema
    from scripts.report_contract import report_contract


@dataclass(frozen=True)
class SchemaRequirement:
    name: str
    any_keywords: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ReportSchema:
    report_type: str
    display_name: str
    market_scope: str
    requirements: tuple[SchemaRequirement, ...]


SHARED_REQUIREMENTS: tuple[SchemaRequirement, ...] = (
    SchemaRequirement(
        "verdict banner",
        ("Verdict", "总体评级", "核心判定", "估值判断", "仓位建议"),
        "First-screen conclusion block that states the report's main judgment.",
    ),
    SchemaRequirement(
        "snapshot cards",
        ("Snapshot", "快照", "KPI", "核心指标"),
        "First-screen metric cards summarizing the most important report metrics.",
    ),
    SchemaRequirement(
        "executive summary",
        ("Executive Summary", "执行摘要"),
        "Concise conclusion-first summary before detailed analysis.",
    ),
    SchemaRequirement(
        "data sources",
        ("数据来源", "Data Source", "Data Sources"),
        "Explicit source disclosure for market, financial, report, and model data.",
    ),
    SchemaRequirement(
        "disclaimer",
        ("免责声明", "不构成投资建议", "仅供研究参考"),
        "Research-only disclaimer and AI-assisted generation notice.",
    ),
)


QUALITATIVE_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "business quality verdict",
        ("Business Quality Verdict", "商业质量", "护城河"),
        "Top judgment for business quality and moat strength.",
    ),
    SchemaRequirement(
        "quality snapshot",
        ("Quality Snapshot", "质量快照", "5年平均ROE", "护城河评级"),
        "KPI cards for ROE, moat, sustainability, management, cycle, capital intensity, and barriers.",
    ),
    SchemaRequirement(
        "core contradiction and refutation",
        ("核心矛盾", "反证条件", "推翻判断", "重评"),
        "First-screen section that states the core tension and what would refute or downgrade the judgment.",
    ),
    SchemaRequirement(
        "maximum risk",
        ("最大风险", "核心风险", "主要风险", "主要约束"),
        "First-screen risk or constraint that balances the business-quality judgment.",
    ),
    SchemaRequirement(
        "monitoring thresholds",
        ("预警阈值", "触发后的重评动作", "当前值 / 本地证据"),
        "Future observation variables with current evidence, thresholds, and re-evaluation actions.",
    ),
    SchemaRequirement(
        "six dimensions",
        ("维度一", "维度二", "维度三", "维度四", "维度五", "维度六"),
        "D1-D6 qualitative analysis structure.",
    ),
    SchemaRequirement(
        "deep summary",
        ("深度总结", "核心投资逻辑", "优势与风险"),
        "Integrated conclusion that weighs core logic, advantages, and risks.",
    ),
    SchemaRequirement(
        "future observation variables",
        ("未来观察", "观察变量", "监控KPI"),
        "Forward-looking monitoring variables for future review.",
    ),
    SchemaRequirement(
        "structured parameters",
        ("结构化参数", "structured parameters", "moat_rating", "roe_5y_avg"),
        "Machine-readable parameter table for downstream turtle and valuation reports.",
    ),
)


TURTLE_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "strategy verdict",
        ("Strategy Verdict", "OBSERVE", "WAIT", "BUY", "AVOID", "仓位建议"),
        "Top investment action and strategy judgment.",
    ),
    SchemaRequirement(
        "turtle snapshot",
        ("Turtle Snapshot", "穿透回报率", "门槛收益率", "安全边际"),
        "KPI cards for penetrating return, hurdle rate, margin of safety, moat, and risk state.",
    ),
    SchemaRequirement(
        "owner earnings",
        ("Owner Earnings", "所有者收益", "OE"),
        "Owner Earnings bridge from reported profit and maintenance capex.",
    ),
    SchemaRequirement(
        "penetrating return",
        ("穿透回报率", "精算", "粗算"),
        "Penetrating return analysis and credibility distinction between rough and refined calculations.",
    ),
    SchemaRequirement(
        "safety margin",
        ("安全边际", "门槛", "margin of safety"),
        "Comparison between refined return and hurdle rate.",
    ),
    SchemaRequirement(
        "value-trap filters",
        ("价值陷阱", "过滤器", "风险等级"),
        "Explicit value-trap checklist and risk rating.",
    ),
    SchemaRequirement(
        "thesis card",
        ("投资论点卡", "Thesis Card", "核心论点"),
        "Investment thesis card with balanced bull/bear framing.",
    ),
    SchemaRequirement(
        "fundamental stop-loss rules",
        ("基本面止损", "止损条件", "critical", "warning"),
        "Structured fundamental stop-loss triggers.",
    ),
    SchemaRequirement(
        "event monitoring checklist",
        ("事件监控", "监控清单", "关键词"),
        "Event and keyword monitoring checklist.",
    ),
)


VALUATION_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "valuation verdict",
        ("Valuation Verdict", "估值判断", "内在价值"),
        "Top valuation state and price-versus-value judgment.",
    ),
    SchemaRequirement(
        "valuation snapshot",
        ("Valuation Snapshot", "估值快照", "安全边际", "WACC"),
        "KPI cards for intrinsic value, safety margin, company type, methods, and WACC.",
    ),
    SchemaRequirement(
        "company classification",
        ("公司分类", "蓝筹", "成长", "混合型"),
        "Company type classification that drives valuation method selection.",
    ),
    SchemaRequirement(
        "method weights",
        ("方法权重", "权重", "估值方法选择"),
        "Selected valuation methods and their weights.",
    ),
    SchemaRequirement(
        "wacc",
        ("WACC", "资本成本", "权益成本"),
        "Capital cost calculation and risk adjustment.",
    ),
    SchemaRequirement(
        "qualitative adjustments",
        ("定性调整", "调整依据", "原模型值", "调整后"),
        "Mapping from qualitative conclusions to model assumptions.",
    ),
    SchemaRequirement(
        "dcf",
        ("DCF", "自由现金流", "永续增长率"),
        "DCF assumptions, result, and sensitivity analysis.",
    ),
    SchemaRequirement(
        "pe band",
        ("PE Band", "PE", "历史分位"),
        "Market multiple valuation using historical PE bands.",
    ),
    SchemaRequirement(
        "ddm",
        ("DDM", "股息", "DPS", "分红"),
        "Dividend discount model with payout and growth explanation.",
    ),
    SchemaRequirement(
        "cross-validation",
        ("交叉验证", "CV", "一致性"),
        "Weighted cross-validation across valuation methods.",
    ),
    SchemaRequirement(
        "reverse valuation",
        ("反向估值", "隐含", "市场预期"),
        "Reverse valuation from market price to implied expectations.",
    ),
    SchemaRequirement(
        "valuation range",
        ("估值区间", "保守", "中性", "乐观"),
        "Final valuation range and current price position.",
    ),
)


REPORT_SCHEMAS: dict[str, ReportSchema] = {
    "qualitative": ReportSchema(
        report_type="qualitative",
        display_name="商业质量评估报告",
        market_scope=report_contract("qualitative")["market_scope"],
        requirements=QUALITATIVE_REQUIREMENTS,
    ),
    "turtle": ReportSchema(
        report_type="turtle",
        display_name="龟龟投资策略分析报告",
        market_scope=report_contract("turtle")["market_scope"],
        requirements=TURTLE_REQUIREMENTS,
    ),
    "valuation": ReportSchema(
        report_type="valuation",
        display_name="估值分析报告",
        market_scope=report_contract("valuation")["market_scope"],
        requirements=VALUATION_REQUIREMENTS,
    ),
}
