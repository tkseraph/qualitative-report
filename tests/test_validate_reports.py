from pathlib import Path

from validate_reports import validate_markdown, validate_output_dir


VALID_QUALITATIVE = """
# 上港集团 · 商业质量评估报告

## Business Quality Verdict
商业质量较强，护城河评级较强。核心优势是港口区位和规模网络，最大风险是外贸周期与吞吐量下行压力。

## Quality Snapshot
5年平均ROE、护城河评级、可持续性、管理层评价、资本强度、周期性。

## Executive Summary
公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。

## 核心矛盾与反证条件
核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。
反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。

## 维度一：商业模式与资本特征
结论：公司商业模式清晰，核心优势来自港口区位和吞吐网络，但资本开支和周期波动需要跟踪。

## 维度二：竞争优势与护城河
结论：护城河较强，来源于稀缺港口资源、网络规模和区域集疏运体系。

## 维度三：外部环境
结论：外部环境与贸易周期相关，监管风险中低，周期下行是主要风险。

## 维度四：管理层与治理
结论：治理整体稳健，资本配置和分红纪律可接受，但关联交易仍需跟踪。

## 维度五：MD&A 解读
结论：管理层叙事与经营数据大体一致，后续需验证吞吐量与费率表现。

## 维度六：控股结构分析
结论：集团结构需要关注，但当前不构成核心折价因素。

## 深度总结
核心投资逻辑是稀缺港口资产带来稳定现金流，优势在区位、规模与网络，风险在外贸周期、资本开支和费率弹性。

## 未来观察变量
| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|
| 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |
| 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |
| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |

## 结构化参数
| 参数 | 取值 |
|---|---|
| moat_rating | 较强 |
| roe_5y_avg | 10% |

## 数据来源
年报与 Tushare。

## 免责声明
仅供研究参考，不构成投资建议。
"""


VALID_TURTLE = """
# 上港集团 · 龟龟投资策略分析报告

## Strategy Verdict
OBSERVE，仓位建议为观察。

## Turtle Snapshot
穿透回报率、门槛收益率、安全边际。

## Executive Summary
当前安全边际不足。

## Owner Earnings
所有者收益 OE 计算。

## 穿透回报率分析
精算与粗算穿透回报率。

## 安全边际
安全边际低于门槛。

## 价值陷阱排查
过滤器与风险等级。

## 投资论点卡（Thesis Card）
核心论点。

## 基本面止损条件
warning 与 critical 条件。

## 事件监控清单
关键词监控。

## 数据来源
年报与 Tushare。

## 免责声明
仅供研究参考，不构成投资建议。
"""


VALID_VALUATION = """
# 上港集团 · 估值分析报告

## Valuation Verdict
估值判断：合理，内在价值接近当前价格。

## Valuation Snapshot
估值快照：安全边际、WACC。

## Executive Summary
估值结论前置。

## 一、公司分类
蓝筹、成长、混合型。

## 估值方法选择
方法权重。

## 二、WACC 计算
资本成本与权益成本。

## 三、定性调整说明
原模型值、调整后、调整依据。

## 方法 1: DCF
自由现金流与永续增长率。

## 方法 2: PE Band
PE 历史分位。

## 方法 3: DDM
股息、DPS、分红。

## 五、交叉验证
CV 与一致性。

## 六、反向估值
市场隐含预期。

## 七、估值结论
估值区间：保守、中性、乐观。

## 数据来源
年报与 Tushare。

## 免责声明
仅供研究参考，不构成投资建议。
"""


def test_valid_qualitative_report_passes():
    result = validate_markdown(VALID_QUALITATIVE, "qualitative")
    assert result.ok
    assert result.missing == []


def test_valid_qualitative_report_accepts_primary_risk_wording():
    text = VALID_QUALITATIVE.replace(
        "最大风险是外贸周期与吞吐量下行压力",
        "主要风险是外贸周期与吞吐量下行压力",
    ).replace(
        "主要约束是吞吐量和费率弹性有限",
        "关键压力是吞吐量和费率弹性有限",
    )
    result = validate_markdown(text, "qualitative")

    assert result.ok
    assert result.missing == []


def test_valid_qualitative_report_accepts_refutation_language_without_repeated_labels():
    text = VALID_QUALITATIVE.replace(
        "核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。",
        "区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级；若核心港区份额持续下降，则推翻判断。",
    )
    result = validate_markdown(text, "qualitative")

    assert result.ok
    assert result.missing == []


def test_qualitative_report_requires_core_contradiction_and_refutation_section():
    text = VALID_QUALITATIVE.replace(
        "## 核心矛盾与反证条件\n核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。\n\n",
        "",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "core_contradiction_refutation" in result.missing
    assert any("core contradiction" in message.lower() or "反证" in message for message in result.messages)


def test_qualitative_report_requires_future_observation_thresholds():
    text = VALID_QUALITATIVE.replace(
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |",
        "监控KPI。",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing
    assert any("Future observation" in message or "观察变量" in message for message in result.messages)


def test_qualitative_report_requires_future_observation_action_language():
    text = VALID_QUALITATIVE.replace(
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |",
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 处理说明 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 记录变化 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 记录变化 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 记录变化 |",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_report_requires_future_observation_threshold_language_when_action_exists():
    text = VALID_QUALITATIVE.replace(
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |",
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 触发后的重评动作 |\n|---|---|---|\n| 5年平均ROE | 10% | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 重评周期位置 |\n| 资本开支 | 可控 | 重评现金质量 |",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_report_requires_future_observation_current_evidence_language():
    text = VALID_QUALITATIVE.replace(
        "| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |",
        "| 观察变量 / 监控KPI | 预警阈值 | 触发后的重评动作 |\n|---|---|---|\n| 5年平均ROE | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_first_screen_requires_advantage_and_risk():
    text = VALID_QUALITATIVE.replace(
        "商业质量较强，护城河评级较强。核心优势是港口区位和规模网络，最大风险是外贸周期与吞吐量下行压力。",
        "商业质量较强，护城河评级较强。公司经营稳健。",
    ).replace(
        "公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。",
        "公司经营稳健，资产质量较好。",
    ).replace(
        "核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。",
        "核心矛盾：区位和规模优势支持稳定现金流。\n反证条件：若港区份额下降，应复核护城河评级。",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_first_screen_balance" in result.missing
    assert any("first-screen" in message.lower() for message in result.messages)


def test_valid_turtle_report_passes():
    result = validate_markdown(VALID_TURTLE, "turtle")
    assert result.ok
    assert result.missing == []


def test_valid_valuation_report_passes():
    result = validate_markdown(VALID_VALUATION, "valuation")
    assert result.ok
    assert result.missing == []


def test_generic_executive_summary_fails_finished_report_quality_check():
    text = VALID_TURTLE.replace("当前安全边际不足。", "内容。")
    result = validate_markdown(text, "turtle")

    assert not result.ok
    assert "generic_executive_summary" in result.missing
    assert any("Executive Summary" in message for message in result.messages)


def test_missing_requirement_fails_with_actionable_message():
    text = VALID_VALUATION.replace("## 方法 3: DDM\n股息、DPS、分红。\n", "")
    result = validate_markdown(text, "valuation")
    assert not result.ok
    assert "ddm" in result.missing
    assert any("ddm" in message.lower() for message in result.messages)


def test_unknown_report_type_fails():
    result = validate_markdown(VALID_QUALITATIVE, "unknown")
    assert not result.ok
    assert "unknown report type" in result.messages[0].lower()


def test_unreplaced_template_placeholder_fails():
    text = VALID_TURTLE + "\n## 附录\n目标公司：{公司名称}\n"
    result = validate_markdown(text, "turtle")

    assert not result.ok
    assert "template_placeholder" in result.missing
    assert "Unreplaced template placeholder" in result.messages[0]


def test_todo_placeholder_fails():
    text = VALID_VALUATION + "\n## 风险提示\nTODO: 补充风险。\n"
    result = validate_markdown(text, "valuation")

    assert not result.ok
    assert "template_placeholder" in result.missing
    assert "TODO" in result.messages[0]


def test_structured_parameter_braces_do_not_count_as_placeholders():
    text = VALID_QUALITATIVE + '\n## 结构化参数\n| peers | {name: "同行公司", ticker: null} |\n'
    result = validate_markdown(text, "qualitative")

    assert result.ok


def test_negative_dcf_without_demotion_fails():
    text = VALID_VALUATION + """
## DCF 结果
原始 DCF 为 -96.57 元/股。
## 七、估值结论
最终判断：合理。
"""
    result = validate_markdown(text, "valuation")

    assert not result.ok
    assert "negative_dcf_demotion" in result.missing
    assert any("negative DCF" in message for message in result.messages)


def test_turtle_buy_verdict_conflicting_with_wait_guidance_fails():
    text = VALID_TURTLE.replace(
        "OBSERVE，仓位建议为观察。",
        "BUY，仓位建议为买入。",
    ) + """
## 行动建议
当前安全边际不足，低于门槛收益率，应 WAIT / 不建仓。
"""
    result = validate_markdown(text, "turtle")

    assert not result.ok
    assert "turtle_verdict_self_consistency" in result.missing
    assert any("Strategy Verdict" in message for message in result.messages)


def test_valuation_buy_verdict_conflicting_with_negative_safety_margin_fails():
    text = VALID_VALUATION.replace(
        "估值判断：合理，内在价值接近当前价格。",
        "估值判断：低估，建议买入。",
    ) + """
## 七、估值结论
当前价格不便宜，安全边际不足，最终不应给出买入结论。
"""
    result = validate_markdown(text, "valuation")

    assert not result.ok
    assert "valuation_verdict_self_consistency" in result.missing


def test_qualitative_strong_verdict_conflicting_with_weak_moat_summary_fails():
    text = VALID_QUALITATIVE.replace(
        "商业质量较强，护城河评级较强。",
        "商业质量优秀，护城河评级强。",
    ).replace(
        "核心投资逻辑是稀缺港口资产带来稳定现金流，优势在区位、规模与网络，风险在外贸周期、资本开支和费率弹性。",
        "深度总结：公司护城河较弱，竞争优势不明显，质量下滑。",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_verdict_self_consistency" in result.missing


def test_negative_dcf_with_diagnostic_demotion_passes():
    text = VALID_VALUATION + """
## DCF 结果
原始 DCF 为 -96.57 元/股，但这是方法适配性诊断，DCF 已降权，不得机械主导最终估值结论。
## 七、估值结论
最终判断：合理。
"""
    result = validate_markdown(text, "valuation")

    assert result.ok


def test_valuation_high_verdict_can_say_not_a_buy_without_self_consistency_failure():
    text = VALID_VALUATION.replace(
        "估值判断：合理，内在价值接近当前价格。",
        "估值判断：高估，当前安全边际不足，不适合作为估值驱动买入。",
    )
    result = validate_markdown(text, "valuation")

    assert result.ok


def test_negative_turtle_return_without_diagnostic_wait_fails():
    text = VALID_TURTLE.replace("OBSERVE，仓位建议为观察。", "BUY，仓位建议为买入。") + """
## 穿透回报率分析
精算穿透回报率 -2.40%，AA 为负值。
"""
    result = validate_markdown(text, "turtle")

    assert not result.ok
    assert "negative_turtle_return" in result.missing
    assert any("negative AA/GG" in message for message in result.messages)


def test_negative_turtle_return_with_diagnostic_wait_passes():
    text = VALID_TURTLE + """
## 穿透回报率分析
精算穿透回报率 -2.40%，AA/GG 为负值，作为诊断值处理；Strategy Verdict 为 WAIT / 不建仓。
"""
    result = validate_markdown(text, "turtle")

    assert result.ok


def test_turtle_wait_verdict_can_mention_not_buying_without_self_consistency_failure():
    text = VALID_TURTLE.replace(
        "OBSERVE，仓位建议为观察。",
        "WAIT / 不建仓。当前价格已经不是买入就是胜利的价格，应等待。",
    )
    result = validate_markdown(text, "turtle")

    assert result.ok


def test_negative_safety_margin_does_not_count_as_negative_turtle_return():
    text = VALID_TURTLE + """
## 穿透回报率分析
精算穿透回报率 **0.36%** vs 门槛收益率 **3.75%**，安全边际 **-3.39 pct**。
"""
    result = validate_markdown(text, "turtle")

    assert result.ok


def test_negative_dcf_change_percent_does_not_count_as_negative_dcf():
    text = VALID_VALUATION + """
## 五、交叉验证
| 方法 | Python默认 | 调整后 | 变动 | 权重 |
| DCF_Scenarios | 722.62 | 618.66 | -14.39% | 35% |
"""
    result = validate_markdown(text, "valuation")

    assert result.ok


def test_negative_dcf_accepts_equivalent_demotion_wording():
    text = VALID_VALUATION + """
## DCF 结果
原始 DCF 为 -96.57 元/股。负 DCF 是方法适配性诊断，DCF 权重降至 0%，不应主导最终估值结论。
"""
    result = validate_markdown(text, "valuation")

    assert result.ok


def test_negative_turtle_return_allows_observation_buy_trigger_language():
    text = VALID_TURTLE + """
## Strategy Verdict
WAIT / 等待，不建仓。
## 穿透回报率分析
精算穿透回报率 -2.40%，AA/GG 为负值，作为诊断值处理。
## 投资论点卡（Thesis Card）
买入理由（观察状态下的潜在正面因素）：若 AA 转正且 GG 达标，可重新评估。
"""
    result = validate_markdown(text, "turtle")

    assert result.ok


def test_output_dir_validation_passes_when_three_reports_exist(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_turtle_report.md").write_text(VALID_TURTLE, encoding="utf-8")
    (output_dir / "600018_SH_valuation_report.md").write_text(VALID_VALUATION, encoding="utf-8")

    results = validate_output_dir(output_dir)

    assert len(results) == 3
    assert all(result.ok for result in results)


def test_output_dir_validation_reports_missing_turtle_file(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_valuation_report.md").write_text(VALID_VALUATION, encoding="utf-8")

    results = validate_output_dir(output_dir)
    turtle_result = next(result for result in results if result.report_type == "turtle")

    assert not turtle_result.ok
    assert turtle_result.missing == ["file"]
    assert "Missing turtle report" in turtle_result.messages[0]


def test_output_dir_validation_reports_duplicate_report_files(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_copy_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_turtle_report.md").write_text(VALID_TURTLE, encoding="utf-8")
    (output_dir / "600018_SH_valuation_report.md").write_text(VALID_VALUATION, encoding="utf-8")

    results = validate_output_dir(output_dir)
    qualitative_result = next(result for result in results if result.report_type == "qualitative")

    assert not qualitative_result.ok
    assert qualitative_result.missing == ["duplicate_files"]
    assert "Multiple qualitative reports" in qualitative_result.messages[0]


def test_output_dir_validation_reports_inconsistent_report_prefixes(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_turtle_report.md").write_text(VALID_TURTLE, encoding="utf-8")
    (output_dir / "000538_SZ_valuation_report.md").write_text(VALID_VALUATION, encoding="utf-8")

    results = validate_output_dir(output_dir)
    prefix_result = next(result for result in results if result.report_type == "directory")

    assert not prefix_result.ok
    assert prefix_result.missing == ["prefix_mismatch"]
    assert "same code_market prefix" in prefix_result.messages[0]


def test_output_dir_validation_reports_content_identity_mismatch(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_qualitative_report.md").write_text(VALID_QUALITATIVE, encoding="utf-8")
    (output_dir / "600018_SH_turtle_report.md").write_text(VALID_TURTLE.replace("上港集团", "招商银行"), encoding="utf-8")
    (output_dir / "600018_SH_valuation_report.md").write_text(VALID_VALUATION, encoding="utf-8")

    results = validate_output_dir(output_dir)
    identity_result = next(result for result in results if result.report_type == "directory")

    assert not identity_result.ok
    assert identity_result.missing == ["identity_mismatch"]
    assert "same company identity" in identity_result.messages[0]


def test_output_dir_validation_accepts_short_and_legal_company_names(tmp_path):
    output_dir = tmp_path / "000538_yunnan_baiyao"
    output_dir.mkdir()
    qualitative = VALID_QUALITATIVE.replace("上港集团 · 商业质量评估报告", "云南白药集团股份有限公司 — 商业质量评估报告")
    turtle = VALID_TURTLE.replace("上港集团 · 龟龟投资策略分析报告", "龟龟投资策略 · 分析报告：云南白药（000538.SZ）")
    valuation = VALID_VALUATION.replace("上港集团 · 估值分析报告", "估值分析报告：云南白药（000538.SZ）")
    (output_dir / "000538_SZ_qualitative_report.md").write_text(qualitative, encoding="utf-8")
    (output_dir / "000538_SZ_turtle_report.md").write_text(turtle, encoding="utf-8")
    (output_dir / "000538_SZ_valuation_report.md").write_text(valuation, encoding="utf-8")

    results = validate_output_dir(output_dir)

    assert all(result.ok for result in results)


def test_output_dir_validation_accepts_alias_company_names_with_same_stock_code(tmp_path):
    output_dir = tmp_path / "603288_haitian"
    output_dir.mkdir()
    qualitative = VALID_QUALITATIVE.replace("上港集团 · 商业质量评估报告", "佛山市海天调味食品股份有限公司 — 商业质量评估报告（603288.SH）")
    turtle = VALID_TURTLE.replace("上港集团 · 龟龟投资策略分析报告", "龟龟投资策略 · 分析报告：海天味业（603288.SH）")
    valuation = VALID_VALUATION.replace("上港集团 · 估值分析报告", "估值分析报告：海天味业（603288.SH）")
    (output_dir / "603288_SH_qualitative_report.md").write_text(qualitative, encoding="utf-8")
    (output_dir / "603288_SH_turtle_report.md").write_text(turtle, encoding="utf-8")
    (output_dir / "603288_SH_valuation_report.md").write_text(valuation, encoding="utf-8")

    results = validate_output_dir(output_dir)

    assert all(result.ok for result in results)


def test_cli_validates_single_file(tmp_path, capsys):
    from validate_reports import main
    import sys

    report_path = tmp_path / "600018_SH_valuation_report.md"
    report_path.write_text(VALID_VALUATION, encoding="utf-8")
    old_argv = sys.argv
    try:
        sys.argv = ["validate_reports.py", str(report_path), "--type", "valuation"]
        main()
    finally:
        sys.argv = old_argv

    captured = capsys.readouterr()
    assert "[PASS] valuation" in captured.out


def test_cli_exits_nonzero_for_invalid_file(tmp_path):
    from validate_reports import main
    import sys
    import pytest

    report_path = tmp_path / "600018_SH_valuation_report.md"
    report_path.write_text("# incomplete", encoding="utf-8")
    old_argv = sys.argv
    try:
        sys.argv = ["validate_reports.py", str(report_path), "--type", "valuation"]
        with pytest.raises(SystemExit) as exc:
            main()
    finally:
        sys.argv = old_argv

    assert exc.value.code == 1


def test_cli_exits_with_clear_message_for_missing_path(tmp_path):
    from validate_reports import main
    import sys
    import pytest

    missing_path = tmp_path / "missing_output"
    old_argv = sys.argv
    try:
        sys.argv = ["validate_reports.py", str(missing_path)]
        with pytest.raises(SystemExit) as exc:
            main()
    finally:
        sys.argv = old_argv

    assert f"Path not found: {missing_path}" in str(exc.value)


def test_readme_documents_report_validator():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "validate_reports.py" in readme
    assert "三报告成品验收" in readme
