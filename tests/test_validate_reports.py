from validate_reports import validate_markdown


VALID_QUALITATIVE = """
# 上港集团 · 商业质量评估报告

## Business Quality Verdict
商业质量较强，护城河评级较强。

## Quality Snapshot
5年平均ROE、护城河评级、可持续性、管理层评价。

## Executive Summary
公司具备区位和规模优势。

## 维度一：商业模式与资本特征
内容。

## 维度二：竞争优势与护城河
内容。

## 维度三：外部环境
内容。

## 维度四：管理层与治理
内容。

## 维度五：MD&A 解读
内容。

## 维度六：控股结构分析
内容。

## 深度总结
核心投资逻辑，优势与风险。

## 未来观察变量
监控KPI。

## 结构化参数
| parameter | value |
| --- | --- |
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


def test_valid_turtle_report_passes():
    result = validate_markdown(VALID_TURTLE, "turtle")
    assert result.ok
    assert result.missing == []


def test_valid_valuation_report_passes():
    result = validate_markdown(VALID_VALUATION, "valuation")
    assert result.ok
    assert result.missing == []


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
