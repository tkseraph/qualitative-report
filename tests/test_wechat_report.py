from pathlib import Path
import subprocess

import pytest

from wechat_report import (
    auto_digest_from_qualitative,
    build_wxgzh_command,
    create_polished_qualitative_markdown,
    discover_report,
    infer_report_type,
    main,
    polish_qualitative_markdown,
    validate_before_draft,
    validate_wechat_draft_readiness,
    validate_wechat_polish_quality,
    _company_chart_profile,
    _create_wechat_financial_charts,
)


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


VALID_QUALITATIVE = """
# 上港集团（600018.SH）— 商业模式与护城河定性分析

> 分析日期：2026-05-09 | 当前股价：¥5.00 | 总市值：¥1,000亿 | A股

## Business Quality Verdict / 商业质量总体评级

综合判断：**B+ / 较强商业质量**。公司依托稀缺港口区位和网络形成稳定现金流，但外贸周期、资本开支和费率机制限制上行弹性。

| 项目 | 结论 |
|---|---|
| 公司本质 | 区域枢纽港口资产 |
| 商业质量 | B+ / 较强商业质量 |
| 护城河来源 | 区位、规模、网络 |
| 最大风险 | 外贸周期与资本开支 |
| 周期位置 | 中性偏逆风 |
| 反证条件 | 吞吐量连续下滑、自由现金流转负或费率机制恶化 |

## Quality Snapshot / 质量快照

商业质量的核心机器字段需要支持首屏判断。

| 指标 | 结论 |
|---|---|
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |
| management_rating | 合格 |

结论：快照指标说明公司具备较强护城河，但可持续性和管理层仍需持续验证。

## Executive Summary / 执行摘要

上港集团是以港口基础设施和集装箱吞吐网络为核心的区域枢纽型公司，优势来自区位、规模和运营网络，最大约束来自外贸周期与资本开支。

### 五个核心发现

- 区位资产稀缺，支撑基础现金流。
- 规模网络真实，但不是无限定价权。
- 外贸周期是主要盈利波动来源。
- 资本开支会压制自由现金流弹性。
- 若吞吐份额下降，应重评护城河。

## 核心矛盾与反证条件

核心矛盾是稀缺港口资产带来稳定现金流，但费率弹性和吞吐周期限制利润上行。若吞吐量连续下滑、自由现金流转负或费率机制恶化，应重评商业质量。

## 自适应研究计划

上港集团的证据路径应围绕重资产港口资产能否把区位优势转化为现金回报展开。

| 项目 | 判断 | 证据路径 | 反证重点 |
|---|---|---|---|
| 公司类型 | 重资产港口 | 吞吐、费率、Capex、FCF | 外贸周期和资本开支 |
| 核心质量问题 | 稀缺资产能否转化为现金回报 | 收入质量、利润桥、现金转化 | ROE 与 FCF 走弱 |
| 关键因果链 | 区位网络 → 吞吐份额 → 现金流 → 再投资约束 | 同业对比和资本消耗 | 份额下降或现金流恶化 |

投资含义是证据必须服务核心判断，并按公司逻辑选择，而不是机械照搬样板公司的细分分项。

## 样板证据模块

收入、利润、现金、治理与叙事需要共同支持商业质量判断。

| 模块 | 核心证据 | 投资含义 |
|---|---|---|
| 收入质量拆分 | 主营港口收入约 100 亿元，非核心收入不构成主要增长来源 | 收入质量支持基础现金流判断 |
| 利润桥 | 利润变化主要来自吞吐量、费率、成本和费用率，2025 ROE 约 10% | 利润质量需要穿透可持续驱动 |
| 量价成本拆解 | 吞吐量、费率和单位成本共同决定周期位置 | 周期公司不能只看收入增速 |
| 现金转化 | 经营现金流/净利润约 1.1x 与自由现金流共同验证利润含金量 | 现金弱化会降低商业质量 |
| 治理红旗 | 审计意见、关联交易、资本配置和分红纪律未见重大异常 | 治理底线暂可接受 |
| MD&A 叙事 vs 财务证据 | 管理层叙事需要被收入、利润、现金流和资本开支交叉验证 | 只报喜不报忧应降低可信度 |
| 伪优势过滤 | 区位和网络是真优势，周期高盈利不是护城河本身 | 避免把景气高点误判为结构性壁垒 |

结论：这些样板证据模块说明当前评级来自多维交叉验证，而不是单一叙事或单项指标。

## 近五年质量趋势

关键结论是重资产或强周期公司必须把单年判断放回五年趋势里验证，避免把周期某一年误判为长期质量。

| 年份 | ROE | 毛利率 | 净利率 | FCF | Capex/D&A |
|---|---|---|---|---|---|
| 2021 | 11% | 32% | 18% | 25 亿元 | 1.1x |
| 2022 | 10% | 31% | 17% | 22 亿元 | 1.2x |
| 2023 | 9% | 30% | 16% | 18 亿元 | 1.3x |
| 2024 | 10% | 31% | 16% | 20 亿元 | 1.2x |
| 2025 | 10% | 30% | 15% | 19 亿元 | 1.2x |

投资含义是趋势证据能把 ROE、利润率、自由现金流和资本开支放在同一时间轴上，检验商业质量是否只是周期高点。

## 维度一：商业模式与资本特征

**结论：公司是重资产基础设施平台，收入稳定但资本消耗高。**

公司赚钱公式可以压缩为五个变量：收入来源、利润驱动、资本占用、现金转化和关键反证。

| 环节 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 收入来源 | 主营港口收入约 100 亿元 | 主业质量稳定 | 非核心收入占比抬升 |
| 利润驱动 | ROE 约 10% | 利润质量中等偏稳 | 费用率异常上升 |
| 资本占用 | Capex/D&A 需持续跟踪 | 重资产约束存在 | Capex 高于经营现金流 |
| 现金转化 | OCF/净利润约 1.1x | 现金转化可接受 | 应收或自由现金流恶化 |
| 关键反证 | 吞吐、费率、现金流同步走弱 | 推翻稳定现金流判断 | 下调商业质量 |

结论：D1 的投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。

关键结论是单位经济模型把周期公司的量价成本变化落到利润桥。

| 变量 | 当前值 | 判断 | 反证阈值 |
|---|---|---|---|
| 销量 | 吞吐量稳定 | 需求韧性尚可 | 连续两年下滑 |
| 吨价 | 单箱收益基本稳定 | 价格弹性有限 | 单箱收益下降 |
| 吨成本 | 单位成本可控 | 成本优势支持利润 | 成本率明显上升 |
| 吨毛利 | 吨毛利中等 | 利润弹性受周期约束 | 吨毛利收缩 |

投资含义是单位经济模型能把量价成本和现金质量连接起来，避免只看收入规模。

### 本章小结

- 本章结论：重资产平台属性明确。
- 最重要证据：收入主要来自港口主业。
- 观察风险 / 重评触发：资本开支持续高于经营现金流。

## 维度二：竞争优势与护城河

**结论：区位和网络形成较强护城河。**

护城河证伪表的核心，是检验结构性优势能否同时经受反向证据和同业对比。

| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 可持续 KPI |
|---|---|---|---|
| 上港集团 | 枢纽港口网络领先，ROE 约 10% | 费率弹性有限 | 核心港区份额 |
| 宁波港 | 长三角重要港口，盈利稳定 | 区域竞争者强 | 吞吐量份额 |
| 招商港口 | 港口组合分散 | 投资收益影响大，资产结构不同 | 主业利润占比 |

结论：同业对比说明优势真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。

### 本章小结

- 本章结论：优势真实但并非无限定价权。
- 最重要证据：枢纽港网络难以复制。
- 观察风险 / 重评触发：吞吐份额持续下降。

## 维度三：外部环境

**结论：外贸周期决定短期压力。**

外部变量的关键，是它如何传导到收入、利润和评级阈值。

| 外部变量 | 当前阶段 | 财务敏感性 | 预警阈值 | 重评动作 |
|---|---|---|---|---|
| 外贸景气 | 中性偏逆风 | 影响吞吐量 | 连续两年下滑 | 下调周期位置 |
| 费率机制 | 稳定但弹性有限 | 影响毛利率 | 单箱收益下降 | 重评定价权 |
| 成本压力 | 可控但需跟踪 | 影响单位成本 | 成本率明显上升 | 重评利润弹性 |

结论：D3 的投资含义是周期属性会压制成长弹性，异常信号是吞吐量与费率同时走弱。

### 本章小结

- 本章结论：外部环境中性偏逆风。
- 最重要证据：需求受全球贸易影响。
- 观察风险 / 重评触发：出口景气度恶化。

## 维度四：管理层与治理

**结论：治理底线可接受。**

管理层评价需要同时看治理红旗、资本配置和承诺兑现。

| 检查项 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 治理红旗 | 审计意见和关联交易未见重大异常 | 底线可接受 | 关联交易异常扩大 |
| 管理层/控制权 | 控股股东和管理层稳定 | 控制权风险中低 | 控制权或核心管理层异常变化 |
| 资本配置 | 分红和投资纪律稳定 | 股东回报可跟踪 | 并购回报低于资本成本 |
| 承诺兑现 | 经营叙事与吞吐趋势基本一致 | 可信度中等 | 承诺连续落空 |

结论：D4 的投资含义是治理不是当前主要矛盾，但异常关联交易会直接削弱评级。

关键结论是资本配置复盘表把股东回报、再投资和管理层解释放在同一口径下检验。

| 动作 | 金额 | 管理层理由 | 后续结果 | 质量评价 |
|---|---|---|---|---|
| 分红 | 约 20 亿元 | 回报股东 | 2023-2025 股东回报稳定 | 合格 |
| Capex | 约 30 亿元 | 维护港口能力 | 2023-2025 FCF 承压但未失控 | 中性 |
| 投资 | 约 10 亿元 | 补强港口网络 | 2023-2025 回报仍需跟踪 | 观察 |

投资含义是资本配置暂未破坏商业质量，但后续结果若低于资本成本应重评管理层质量；多年复盘状态显示分红兑现较稳、扩张回报仍需验证。

### 本章小结

- 本章结论：管理层评价合格。
- 最重要证据：分红和资本配置稳定。
- 观察风险 / 重评触发：关联交易异常扩大。

## 维度五：MD&A 解读

**结论：管理层叙事与主业数据大体一致。**

管理层叙事审计表的核心，是检验财务证据、风险措辞变化和沉默信息是否一致。

| 管理层说法 | 财务验证 | 是否兑现 | 沉默信息 | 重评动作 |
|---|---|---|---|---|
| 历史指引：枢纽港韧性 | 吞吐与现金流基本匹配 | 实际兑现基本符合上一年目标 | 费率弹性解释不足 | 跟踪单箱收益 |
| 成本管控 | 成本率未见重大失控 | 部分兑现 | 单位成本拆分不足 | 跟踪成本率 |
| 新战略：资本开支 | Capex 仍影响 FCF | 新项目回报仍需验证 | 新项目回报周期披露有限 | 重评投资回报 |

结论：D5 的投资含义是叙事大体可信，但异常点是管理层没有充分解释费率弹性和新增投资回报。

历史目标 vs 实际兑现表可以把上一年经营计划、新战略和当年财务结果放在一起复盘。

| 年份 | 管理层目标 | 实际结果 | 偏差 | 投资含义 |
|---|---|---|---|---|
| 2023 | 稳定吞吐与现金流 | 吞吐和 OCF 基本稳定 | 基本符合 | 叙事可信度中等 |
| 2024 | 推进港口网络投资 | Capex 继续占用现金 | 回报滞后 | 跟踪投资回报 |
| 2025 | 提升运营效率 | 费用率未见失控 | 部分兑现 | 继续验证成本效率 |

投资含义是管理层叙事不是只看口号，而要看目标是否转化为收入、利润和现金流结果；2023-2025 多年兑现状态显示经营目标大体兑现，但投资回报解释仍不充分。

### 本章小结

- 本章结论：叙事可信度中等。
- 最重要证据：经营描述与吞吐量方向一致。
- 观察风险 / 重评触发：叙事与现金流背离。

## 维度六：控股结构分析

**结论：控股结构稳定。**

D6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。

| 触发条件 | 当前证据 | 是否展开 | 投资含义 |
|---|---|---|---|
| 子公司利润占比超过 30% | 未见单一子公司主导利润，计算依据为子公司净利润 / 合并净利润 | 否 | 暂不做 SOTP 主判断 |
| 投资收益占比超过 20% | 投资收益需跟踪但非唯一来源，计算口径为投资收益 / 合并净利润 | 观察 | 防止利润质量被投资收益扭曲 |
| 控制权或质押异常 | 控制关系清晰，母合差异未见异常放大 | 否 | 当前不构成核心折价 |

结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益或子公司利润占比突然放大。

### 本章小结

- 本章结论：股权结构未构成主要风险。
- 最重要证据：实际控制关系清晰。
- 观察风险 / 重评触发：控制权或质押风险变化。

## 交叉验证与深度分析

这组研究层把管理层叙事、财务数字和反向信号放在一起看，避免单一指标误判商业质量。

### 数字与叙事的匹配

关键结论是管理层叙事必须被 ROE、现金流和资本开支同时验证。

| 叙事 | 财务验证 | 冲突 / 反证 |
|---|---|---|
| 稀缺港口资产 | 主营收入约 100 亿元，ROE 约 10% | 资本开支可能压制 FCF |
| 稳定现金流 | OCF/净利润约 1.1x | 外贸周期可能削弱吞吐 |

投资含义是港口区位优势需要同时被收入、利润和现金流验证。

### 核心矛盾

- 稀缺资产 vs 外贸周期：区位优势真实，但吞吐需求仍受周期影响。
- 现金稳定 vs 资本开支：利润有现金支撑，但扩张投入会降低自由现金流弹性。

### 被忽视信号

- 费用率异常变化需要跟踪。
- 投资收益占比和非经营项可能扭曲利润质量。
- 口径差异需要在数据来源中解释。

## 深度总结

公司本质是区域枢纽港口资产。优势真实，因为区位、泊位和网络具有长期稀缺性。最大风险是周期和资本开支共同压低自由现金流。若吞吐份额下降、费率机制恶化或自由现金流持续为负，应重评。

## 未来观察变量

未来观察变量需要聚焦会触发商业质量重评的指标。

| 优先级 | 观察变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|---|
| P0 | 吞吐量 | 年报披露稳定 | 连续两年下降 | 下调增长质量 |
| P0 | 自由现金流 | 仍需观察 | 连续转负 | 重评资本消耗 |
| P1 | 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |
| P2 | 投资收益占比 | 非主导 | 超过 20% | 复核利润质量 |

结论：这些指标若触发预警，意味着商业质量需要按优先级重新评估。

## 报告局限与数据警示

关键结论是报告局限会影响细项置信度，但不直接替代主线商业质量判断。
本报告基于公司年报、结构化市场数据和公开披露信息，部分同业口径与公司披露口径可能存在差异。

| 局限类型 | 当前限制 | 对判断的影响 | 后续复核动作 |
|---|---|---|---|
| 数据口径冲突 | Tushare 与年报可能存在分红或利润口径差异 | 不改变主线判断，但影响细项数值 | 以年报口径为准并标注差异 |
| 同业数据缺口 | 部分竞品全年单位经济数据不可得 | 同业比较置信度下降 | 后续补充可比公司年报 |
| 披露不足事项 | 管理层未量化所有经营目标 | D5 复盘需要保留不确定性 | 跟踪下一年度 MD&A |

投资含义是报告应明确哪些结论来自硬数据，哪些结论仍受披露口径和数据可得性限制。

## 数据来源

年报与本地数据包。

## 免责声明

仅供研究参考，不构成投资建议。

## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| roe_5y_avg | 10% |
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |
| management_rating | 合格 |
| cyclicality | 强周期 |
| cycle_position | 中段 |
| capital_intensity | capital-hungry |
| entry_barrier | 高 |
| moat_existence | 存在 |
"""


def test_qualitative_polish_adds_wechat_hero_card_and_removes_machine_appendix(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    polished = polish_qualitative_markdown(VALID_QUALITATIVE)
    hero = polished.split("## Quality Snapshot", 1)[0]

    assert "## 一句话结论" in hero
    assert "> 上港集团是以港口基础设施" in hero
    assert "**质量评级**：B+ / 较强商业质量" in hero
    assert "**公司本质**：区域枢纽港口资产" in hero
    assert "**护城河来源**：区位、规模、网络" in hero
    assert "**最大风险**：外贸周期与资本开支" in hero
    assert "**未来最该看**：吞吐量连续下滑、自由现金流转负或费率机制恶化" in hero
    assert "### 公司本质" not in hero
    assert "### 商业质量" not in hero
    assert "结构化参数" not in polished
    assert "moat_sustainability" not in polished


def test_qualitative_polish_card_values_strip_markdown_and_avoid_overcapture():
    polished = polish_qualitative_markdown(VALID_QUALITATIVE)

    hero = polished.split("## Quality Snapshot", 1)[0]
    assert "**质量评级**：B+ / 较强商业质量" in hero
    assert "公司依托稀缺港口区位" not in hero


def test_qualitative_polish_inserts_card_when_unrelated_project_table_exists():
    report_with_unrelated_table = VALID_QUALITATIVE + "\n\n## 附加说明\n\n| 项目 | 结论 |\n|---|---|\n| 其他事项 | 不影响首屏摘要卡 |\n"

    polished = polish_qualitative_markdown(report_with_unrelated_table)

    hero = polished.split("## Quality Snapshot", 1)[0]
    assert hero.count("**公司本质**") == 1
    assert "### 其他事项" in polished
    assert "- **结论**：不影响首屏摘要卡" in polished


def test_qualitative_polish_does_not_duplicate_existing_question_answer_card():
    report_with_question_answer_card = """
# 亿联网络（300628.SZ）— 商业模式与护城河定性分析

## Business Quality Verdict / 商业质量总体评级

综合判断：**A- / 高商业质量**。

### 首屏摘要卡

| 问题 | 回答 |
|---|---|
| 公司本质 | 全球企业通信终端公司 |
| 商业质量 | 高商业质量 |
| 护城河来源 | 渠道信任、产品可靠性、平台兼容 |
| 最大风险 | 海外需求与现金转化弱化 |
| 周期位置 | 弱周期但受海外库存周期影响 |
| 反证条件 | 毛利率下滑且现金流持续弱于净利润 |

## Executive Summary / 执行摘要

一句话摘要：亿联网络是一家高盈利、低负债、全球化的企业通信终端公司，优势真实但并非不可撼动，未来三年关键看 AI 会议设备能否延续高毛利增长，同时不牺牲现金转化。

## 结构化参数

| 参数 | 值 |
|---|---|
| moat_rating | 较强 |
"""

    polished = polish_qualitative_markdown(report_with_question_answer_card)

    assert polished.count("## 一句话结论") == 1
    assert "**公司本质**：全球企业通信终端公司" in polished
    assert "**质量评级**：高商业质量" in polished
    assert "### 首屏摘要卡" not in polished
    assert "| 问题 | 回答 |" not in polished
    assert "| 项目 | 结论 |" not in polished


def test_qualitative_polish_adds_wechat_section_dividers_idempotently():
    polished = polish_qualitative_markdown(VALID_QUALITATIVE)
    repolished = polish_qualitative_markdown(polished)

    assert "---\n\n## Executive Summary / 执行摘要" in polished
    assert "---\n\n## 维度一：商业模式与资本特征" in polished
    assert "---\n\n## 深度总结" in polished
    assert polished.count("---\n\n## Executive Summary / 执行摘要") == 1
    assert repolished == polished


def test_qualitative_polish_removes_local_data_boundary_and_simplifies_sources():
    report = VALID_QUALITATIVE.replace(
        "> 分析日期：2026-05-09 | 当前股价：¥5.00 | 总市值：¥1,000亿 | A股",
        "> 分析日期：2026-05-09 | 当前股价：¥5.00 | 总市值：¥1,000亿 | A股  \n> 数据边界：仅使用本地 `data_pack_market.md`、`annual_report.pdf`、`pdf_sections.json` 及 prompt 指定 reference 文件；未联网、未使用外部新增样本。\n> 核心数据来源：2025 年年度报告 PDF、本地 Tushare 数据包、PDF 附注抽取文件。",
    ).replace(
        "年报与本地数据包。",
        "- output/300628_yilian_chain_regression/data_pack_market.md\n- output/300628_yilian_chain_regression/annual_report.pdf\n- output/300628_yilian_chain_regression/pdf_sections.json\n- shared/qualitative/references/output_schema.md",
    ).replace(
        "**结论：控股结构稳定。**",
        "**结论：控股结构稳定。** 本节依据本地证据、PDF 附注抽取文件、本地 Tushare 数据与本地输入交叉验证，不向读者展示本地文件名。",
    )

    polished = polish_qualitative_markdown(report)

    assert "数据边界" not in polished
    assert "data_pack_market.md" not in polished
    assert "annual_report.pdf" not in polished
    assert "pdf_sections.json" not in polished
    assert "shared/qualitative" not in polished
    assert "本地数据包" not in polished
    assert "本地 Tushare 数据" not in polished
    assert "PDF 附注抽取文件" not in polished
    assert "本地证据" not in polished
    assert "本地输入" not in polished
    assert "核心数据来源：公司年报、年报附注与 Tushare 财务及市场数据。" in polished
    assert "基于上市公司年报和 Tushare 数据。" in polished


def test_qualitative_polish_uses_layered_table_strategy_for_wechat():
    report = VALID_QUALITATIVE + """
## 业务结构

| 业务 | 收入占比 | 毛利率 | 判断 |
|---|---:|---:|---|
| 主业A | 70% | 35% | 核心利润池 |
| 主业B | 30% | 20% | 第二曲线 |

## 宽表

| 指标 | 2025 | 2024 | 2023 | 2022 | 2021 |
|---|---:|---:|---:|---:|---:|
| ROE | 10% | 9% | 8% | 7% | 6% |
"""
    polished = polish_qualitative_markdown(report)

    assert "| 项目 | 结论 |" not in polished
    assert "**公司本质**：区域枢纽港口资产" in polished
    assert "| 业务 | 收入占比 | 毛利率 | 判断 |" in polished
    assert "| 主业A | 70% | 35% | 核心利润池 |" in polished
    assert "| 指标 | 2025 | 2024 | 2023 | 2022 | 2021 |" not in polished
    assert "### ROE" in polished
    assert "- **2025**：10%" in polished


def test_qualitative_polish_converts_long_mobile_tables_without_heading_stack():
    report = VALID_QUALITATIVE + """
## 多指标快照

| 指标 | 当前判断 | 关键证据 | 含义 |
|---|---|---|---|
| ROE | 中等 | 五年均值回落 | 回报承压 |
| 护城河 | 较强 | 渠道和成本 | 优势真实 |
| 管理层 | 合格 | 分红稳定 | 治理可接受 |
| 周期 | 逆风 | 需求下降 | 估值需折价 |
"""

    polished = polish_qualitative_markdown(report)

    assert "wechat_heading_stack" not in validate_wechat_polish_quality(polished)
    assert "**ROE**" in polished
    assert "- **当前判断**：中等" in polished
    assert "### ROE" not in polished


def test_qualitative_preview_html_exits_when_draft_readiness_fails(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(
        VALID_QUALITATIVE.replace(
            "## Executive Summary / 执行摘要",
            "## 额外图表\n\n![缺图](charts/missing.png)\n\n**读图结论**：缺图应阻止草稿生成。\n\n## Executive Summary / 执行摘要",
        ),
        encoding="utf-8",
    )

    with pytest.raises(SystemExit) as excinfo:
        main([str(report_path), "--qualitative-polish", "--preview-html", "--skip-validation", "--dry-run"])

    assert "WeChat draft readiness failed" in str(excinfo.value)
    assert "wechat_missing_image_asset" in str(excinfo.value)


def test_validate_wechat_draft_readiness_rejects_final_html_table_overflow_and_missing_images(tmp_path):
    polished_path = tmp_path / "report.polished.md"
    preview_path = tmp_path / "report.preview.html"
    polished_path.write_text(
        """
# 测试公司商业质量分析

## 一句话结论

**质量评级**：较强
**公司本质**：制造企业
**护城河来源**：规模
**最大风险**：需求下滑
**未来最该看**：现金流

## 关键财务趋势图

![收入利润趋势：收入增长是否同步转化为利润](charts/missing.png)

**读图结论**：收入改善。
""",
        encoding="utf-8",
    )
    preview_path.write_text("<html><table style='white-space: nowrap'></table></html>", encoding="utf-8")

    issues = validate_wechat_draft_readiness(polished_path, preview_path)

    assert "wechat_preview_table_overflow" in issues
    assert "wechat_missing_image_asset" in issues


def test_validate_wechat_polish_quality_allows_bulleted_kpi_heading_groups():
    polished = """
# 测试公司商业质量分析

## 一句话结论

**质量评级**：较强
**公司本质**：制造企业
**护城河来源**：规模
**最大风险**：需求下滑
**未来最该看**：现金流

### 毛利率
- **当前值 / 本地证据**：60%
- **预警阈值**：低于 55%

### 研发费用率
- **当前值 / 本地证据**：8%
- **预警阈值**：低于 6%

### 产品收入占比
- **当前值 / 本地证据**：40%
- **预警阈值**：停滞

### 本章小结
- **本章结论**：仍需观察。
"""

    assert validate_wechat_polish_quality(polished) == []


def test_validate_wechat_polish_quality_rejects_missing_article_design():
    poor_polish = """
# 测试公司商业质量分析

## Business Quality Verdict / 商业质量总体评级

### 公司本质
- **结论**：制造企业

### 商业质量
- **结论**：中等

### 护城河来源
- **结论**：规模

### 最大风险
- **结论**：需求下滑

## 关键财务趋势图

![营业收入与归母净利润](charts/revenue_profit.png)

## Executive Summary / 执行摘要

摘要。
"""

    issues = validate_wechat_polish_quality(poor_polish)

    assert "wechat_hero_card" in issues
    assert "wechat_chart_reading" in issues
    assert "wechat_heading_stack" in issues


def test_validate_wechat_polish_quality_accepts_polished_article_design(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    (tmp_path / "data_pack_market.md").write_text(
        """
# 数据包 — 600018.SH

## 3. 合并利润表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 10,000.00 | 9,000.00 | 8,000.00 |
| 归母净利润 | 2,000.00 | 1,800.00 | 1,500.00 |

## 5. 现金流量表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 自由现金流 (FCF) | 1,500.00 | 1,200.00 | 900.00 |

## 8. 财务指标

| 指标 | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| ROE (%) | 10.00 | 9.00 | 8.00 |
""",
        encoding="utf-8",
    )

    polished = create_polished_qualitative_markdown(report_path, tmp_path / ".wxgzh").read_text(encoding="utf-8")

    assert validate_wechat_polish_quality(polished) == []


def test_qualitative_polish_splits_overlong_body_lines_without_touching_code():
    overlong_line = "这一段把收入结构、经营数据、商业含义、风险触发和重评动作全部塞在同一行里，没有分段，也没有用列表承接关键信息，读者在微信公众号窄屏里会看到一整块密集文字，因此展示层 polish 应该把它拆成更短的段落；表格和代码块不能被拆，因为它们有自己的结构。"
    report = VALID_QUALITATIVE + f"""
## 附加说明

{overlong_line}

```yaml
note: {overlong_line}
```
"""

    polished = polish_qualitative_markdown(report)
    lines = polished.splitlines()

    assert overlong_line not in [line.strip() for line in lines]
    assert all(
        len(line.strip()) <= 100
        for line in lines
        if line.strip()
        and not line.strip().startswith(("#", "```"))
        and "note:" not in line
        and "/" not in line
    )
    assert f"note: {overlong_line}" in polished


def test_create_polished_qualitative_markdown_writes_copy_without_changing_original(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    output_dir = tmp_path / ".wxgzh"

    polished_path = create_polished_qualitative_markdown(report_path, output_dir)

    assert polished_path == output_dir / "600018_SH_qualitative_report.polished.md"
    assert polished_path.exists()
    assert report_path.read_text(encoding="utf-8") == VALID_QUALITATIVE
    assert "结构化参数" not in polished_path.read_text(encoding="utf-8")


def test_create_wechat_financial_charts_uses_mixed_axes_and_chinese_money_units(tmp_path, monkeypatch):
    calls = []

    def fake_combo_chart(path, years, bars, lines, left_ylabel, right_ylabel):
        calls.append((path.name, bars, lines, left_ylabel, right_ylabel))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"chart")

    def fake_line_chart(path, years, series, ylabel):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"chart")

    monkeypatch.setattr("wechat_report._write_bar_line_chart", fake_combo_chart)
    monkeypatch.setattr("wechat_report._write_line_chart", fake_line_chart)

    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    (tmp_path / "data_pack_market.md").write_text(
        """
# 数据包 — 600018.SH

## 3. 合并利润表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 10,000.00 | 9,000.00 | 8,000.00 |
| 归母净利润 | 2,000.00 | 1,800.00 | 1,500.00 |

## 5. 现金流量表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 自由现金流 (FCF) | 1,500.00 | 1,200.00 | 900.00 |

## 8. 财务指标

| 指标 | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| ROE (%) | 10.00 | 9.00 | 8.00 |
""",
        encoding="utf-8",
    )

    _create_wechat_financial_charts(report_path, tmp_path / ".wxgzh")

    revenue_call = next(call for call in calls if call[0] == "revenue_profit.png")
    fcf_call = next(call for call in calls if call[0] == "fcf_roe.png")
    assert [label for label, _ in revenue_call[1]] == ["营业收入", "归母净利润"]
    assert [label for label, _ in revenue_call[2]] == ["营业收入同比", "归母净利润同比"]
    assert revenue_call[3] == "亿元"
    assert revenue_call[4] == "%"
    assert [label for label, _ in fcf_call[1]] == ["自由现金流"]
    assert [label for label, _ in fcf_call[2]] == ["ROE"]
    assert fcf_call[3] == "亿元"
    assert fcf_call[4] == "%"


def test_qualitative_dry_run_rejects_stale_polished_copy_when_source_changes(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    stale_dir = tmp_path / ".wxgzh"
    stale_dir.mkdir()
    stale_polished = stale_dir / "600018_SH_qualitative_report.polished.md"
    stale_polished.write_text("# 旧草稿\n\n## 结构化参数\n旧内容", encoding="utf-8")

    main([str(report_path), "--skip-validation", "--dry-run"])

    polished = stale_polished.read_text(encoding="utf-8")
    assert "旧草稿" not in polished
    assert "## 结构化参数" not in polished
    assert "## 一句话结论" in polished


def test_qualitative_draft_readiness_rejects_chart_section_without_assets(tmp_path):
    polished_path = tmp_path / "report.polished.md"
    polished_path.write_text(
        """
# 测试公司商业质量分析

## 一句话结论

**质量评级**：较强
**公司本质**：制造企业
**护城河来源**：规模
**最大风险**：需求下滑
**未来最该看**：现金流

## 关键财务趋势图

### 收入利润趋势：收入增长是否同步转化为利润

**读图结论**：收入改善。
""",
        encoding="utf-8",
    )

    issues = validate_wechat_draft_readiness(polished_path)

    assert "wechat_chart_section_without_images" in issues


def test_create_polished_qualitative_markdown_inserts_generic_charts_from_data_pack(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    (tmp_path / "data_pack_market.md").write_text(
        """
# 数据包 — 600018.SH

## 3. 合并利润表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 10,000.00 | 9,000.00 | 8,000.00 |
| 归母净利润 | 2,000.00 | 1,800.00 | 1,500.00 |

## 5. 现金流量表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 自由现金流 (FCF) | 1,500.00 | 1,200.00 | 900.00 |

## 8. 财务指标

| 指标 | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| ROE (%) | 10.00 | 9.00 | 8.00 |
""",
        encoding="utf-8",
    )
    output_dir = tmp_path / ".wxgzh"

    polished_path = create_polished_qualitative_markdown(report_path, output_dir)
    polished = polished_path.read_text(encoding="utf-8")

    assert "## 关键财务趋势图" in polished
    assert "### 收入利润趋势：收入增长是否同步转化为利润" in polished
    assert "![收入利润趋势：收入增长是否同步转化为利润](charts/revenue_profit.png)" in polished
    assert "**读图结论**：营业收入和归母净利润同向改善" in polished
    assert "### 现金回报趋势：利润是否有现金和 ROE 支撑" in polished
    assert "![现金回报趋势：利润是否有现金和 ROE 支撑](charts/fcf_roe.png)" in polished
    assert "**读图结论**：自由现金流和 ROE 同步改善" in polished
    assert (output_dir / "charts" / "revenue_profit.png").exists()
    assert (output_dir / "charts" / "fcf_roe.png").exists()


def test_company_chart_profile_prefers_structured_profile_over_hypothetical_cycle_mentions():
    md_text = """
## Executive Summary / 执行摘要

亿联网络不是重资产通信设备制造商，而是轻资产企业通信平台。它不像资源品那样强周期。
如果行业处于高景气强周期，利润现金流应同步改善。

## 结构化参数（机器读取 / 附录）

```yaml
D1_business_model:
  capital_intensity: capital-light
D3_external_environment:
  cyclicality: 弱周期
```
"""

    assert _company_chart_profile(md_text) == "light_asset"


def test_create_polished_qualitative_markdown_adds_type_specific_chart_for_cycle_company(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    report_path.write_text(
        VALID_QUALITATIVE.replace(
            "**结论：公司是重资产基础设施平台，收入稳定但资本消耗高。**",
            "**结论：公司不是轻资产成长股，而是强周期重资产基础设施平台，收入稳定但资本消耗高。** 应收和存货也会影响现金流。",
        ),
        encoding="utf-8",
    )
    (tmp_path / "data_pack_market.md").write_text(
        """
# 数据包 — 600585.SH

## 3. 合并利润表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 10,000.00 | 9,000.00 | 8,000.00 |
| 归母净利润 | 2,000.00 | 1,800.00 | 1,500.00 |

## 5. 现金流量表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 经营现金流 | 2,400.00 | 2,100.00 | 1,700.00 |
| 自由现金流 (FCF) | 1,500.00 | 1,200.00 | 900.00 |

## 8. 财务指标

| 指标 | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| ROE (%) | 10.00 | 9.00 | 8.00 |
| 毛利率 (%) | 27.00 | 25.00 | 23.00 |
""",
        encoding="utf-8",
    )

    polished = create_polished_qualitative_markdown(report_path, tmp_path / ".wxgzh").read_text(encoding="utf-8")

    assert "### 周期质量趋势：ROE 与毛利率是否同步修复" in polished
    assert "![周期质量趋势：ROE 与毛利率是否同步修复](charts/cycle_quality.png)" in polished
    assert (tmp_path / ".wxgzh" / "charts" / "cycle_quality.png").exists()


def test_create_polished_qualitative_markdown_adds_type_specific_chart_for_light_asset_company(tmp_path):
    report_path = tmp_path / "300628_SZ_qualitative_report.md"
    report_path.write_text(
        VALID_QUALITATIVE.replace("capital-hungry", "轻资产")
        .replace("强周期", "弱周期")
        .replace("重资产基础设施平台", "轻资产企业通信终端平台")
        .replace("重资产平台属性明确", "轻资产平台属性明确，不是重资产制造商，也不是强周期资源品")
        + "\n\n补充判断：这更像弱周期扩张，而非强周期全面上行；如果行业处于高景气强周期，利润现金流应同步改善。",
        encoding="utf-8",
    )
    (tmp_path / "data_pack_market.md").write_text(
        """
# 数据包 — 300628.SZ

## 3. 合并利润表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 10,000.00 | 9,000.00 | 8,000.00 |
| 归母净利润 | 2,000.00 | 1,800.00 | 1,500.00 |

## 5. 现金流量表

| 项目 (百万元) | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 经营现金流 | 1,200.00 | 1,500.00 | 1,300.00 |
| 自由现金流 (FCF) | 1,100.00 | 1,400.00 | 1,200.00 |

## 8. 财务指标

| 指标 | 2025 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| ROE (%) | 10.00 | 9.00 | 8.00 |
| 应收账款 | 1,500.00 | 1,000.00 | 800.00 |
| 存货 | 1,200.00 | 900.00 | 700.00 |
""",
        encoding="utf-8",
    )

    polished = create_polished_qualitative_markdown(report_path, tmp_path / ".wxgzh").read_text(encoding="utf-8")

    assert "### 现金转化趋势：利润是否被应收和存货占用" in polished
    assert "![现金转化趋势：利润是否被应收和存货占用](charts/cash_conversion.png)" in polished
    assert (tmp_path / ".wxgzh" / "charts" / "cash_conversion.png").exists()


def test_auto_digest_from_qualitative_prefers_executive_summary_and_is_length_limited():
    digest = auto_digest_from_qualitative(VALID_QUALITATIVE)

    assert digest.startswith("上港集团是以港口基础设施")
    assert len(digest) <= 80


def test_auto_digest_from_qualitative_removes_common_summary_prefixes():
    report = VALID_QUALITATIVE.replace(
        "上港集团是以港口基础设施和集装箱吞吐网络为核心的区域枢纽型公司，优势来自区位、规模和运营网络，最大约束来自外贸周期与资本开支。",
        "一句话摘要：上港集团是区域枢纽港口公司，优势来自区位与网络，最大约束来自外贸周期。",
    )

    digest = auto_digest_from_qualitative(report)

    assert digest == "上港集团是区域枢纽港口公司，优势来自区位与网络，最大约束来自外贸周期。"
    assert "一句话摘要" not in digest


def test_auto_digest_from_qualitative_falls_back_to_verdict_then_title():
    without_summary = VALID_QUALITATIVE.replace(
        "## Executive Summary / 执行摘要\n\n上港集团是以港口基础设施和集装箱吞吐网络为核心的区域枢纽型公司，优势来自区位、规模和运营网络，最大约束来自外贸周期与资本开支。\n\n",
        "",
    )
    verdict_digest = auto_digest_from_qualitative(without_summary)
    assert verdict_digest.startswith("综合判断")

    title_only = "# 测试公司（000001.SZ）— 商业模式与护城河定性分析\n"
    assert auto_digest_from_qualitative(title_only) == "测试公司（000001.SZ）商业质量定性分析"


def test_discovers_turtle_report_from_output_dir(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    report_path = output_dir / "600018_SH_turtle_report.md"
    report_path.write_text(VALID_TURTLE, encoding="utf-8")

    result = discover_report(output_dir, "turtle", None)

    assert result == report_path


def test_discovery_fails_on_duplicate_reports(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    (output_dir / "600018_SH_turtle_report.md").write_text(VALID_TURTLE, encoding="utf-8")
    (output_dir / "600018_SH_copy_turtle_report.md").write_text(VALID_TURTLE, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        discover_report(output_dir, "turtle", None)

    assert "Multiple turtle reports" in str(exc.value)


def test_infer_report_type_from_canonical_filename():
    assert infer_report_type(Path("600018_SH_qualitative_report.md")) == "qualitative"
    assert infer_report_type(Path("600018_SH_turtle_report.md")) == "turtle"
    assert infer_report_type(Path("600018_SH_valuation_report.md")) == "valuation"


def test_validate_before_draft_rejects_invalid_finished_report(tmp_path):
    report_path = tmp_path / "600018_SH_turtle_report.md"
    report_path.write_text("# incomplete", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        validate_before_draft(report_path, "turtle")

    assert "Report validation failed" in str(exc.value)


def test_build_wxgzh_command_uses_npx_package_and_draft_safe_flags(tmp_path):
    report_path = tmp_path / "600018_SH_turtle_report.md"
    output_dir = tmp_path / ".wxgzh"

    command = build_wxgzh_command(
        report_path,
        output_dir=output_dir,
        account="turtle",
        author="龟龟投资框架",
        digest="上港集团跟踪",
        theme="blue",
        cover=None,
        no_cover=False,
    )

    assert command[:4] == ["npx", "-y", "@lyhue1991/wxgzh", str(report_path)]
    assert "--output-dir" in command
    assert str(output_dir) in command
    assert "--account" in command
    assert "turtle" in command
    assert "--author" in command
    assert "龟龟投资框架" in command
    assert "--digest" in command
    assert "上港集团跟踪" in command
    assert "--theme" in command
    assert "blue" in command
    assert "publish" not in command
    assert "submit" not in command


def test_parse_args_rejects_credential_like_unknown_args(tmp_path):
    report_path = tmp_path / "600018_SH_turtle_report.md"
    report_path.write_text(VALID_TURTLE, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(report_path), "--appid", "abc", "--dry-run"])

    assert "Credential-like arguments are not supported" in str(exc.value)


def test_dry_run_prints_command_without_subprocess(tmp_path, monkeypatch, capsys):
    report_path = tmp_path / "600018_SH_turtle_report.md"
    report_path.write_text(VALID_TURTLE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--dry-run"])

    captured = capsys.readouterr()
    assert "npx -y @lyhue1991/wxgzh" in captured.out
    assert str(report_path) in captured.out


def test_qualitative_dry_run_uses_polished_markdown_and_auto_digest_by_default(tmp_path, monkeypatch, capsys):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--skip-validation", "--dry-run"])

    captured = capsys.readouterr()
    polished_path = tmp_path / ".wxgzh" / "600018_SH_qualitative_report.polished.md"
    assert str(polished_path) in captured.out
    assert str(report_path) not in captured.out
    assert "--digest" in captured.out
    assert "上港集团是以港口基础设施" in captured.out
    assert polished_path.exists()
    assert "## 结构化参数" not in polished_path.read_text(encoding="utf-8")
    assert report_path.read_text(encoding="utf-8") == VALID_QUALITATIVE


def test_preview_html_with_qualitative_polish_writes_preview_without_network(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("preview dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--qualitative-polish", "--preview-html", "--skip-validation", "--dry-run"])

    preview_path = tmp_path / ".wxgzh" / "600018_SH_qualitative_report.preview.html"
    assert preview_path.exists()
    html = preview_path.read_text(encoding="utf-8")
    assert "核心矛盾与反证条件" in html
    assert "未来观察变量" in html
    assert "结构化参数" not in html


def test_preview_html_uses_default_qualitative_polish(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("preview dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--preview-html", "--skip-validation", "--dry-run"])

    preview_path = tmp_path / ".wxgzh" / "600018_SH_qualitative_report.preview.html"
    assert preview_path.exists()
    assert "结构化参数" not in preview_path.read_text(encoding="utf-8")


def test_explicit_digest_wins_over_auto_digest_in_qualitative_polish(tmp_path, capsys):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    main([str(report_path), "--qualitative-polish", "--digest", "人工摘要", "--skip-validation", "--dry-run"])

    captured = capsys.readouterr()
    assert "--digest" in captured.out
    assert "人工摘要" in captured.out
    assert "上港集团是以港口基础设施" not in captured.out


def test_qualitative_polish_runs_validation_before_writing_polished_copy(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    events = []

    def fake_validate(path, report_type):
        events.append(("validate", path.name, report_type))

    original_create = create_polished_qualitative_markdown

    def wrapped_create(path, output_dir):
        events.append(("polish", path.name, output_dir.name))
        return original_create(path, output_dir)

    monkeypatch.setattr("wechat_report.validate_before_draft", fake_validate)
    monkeypatch.setattr("wechat_report.create_polished_qualitative_markdown", wrapped_create)

    main([str(report_path), "--dry-run"])

    assert events[:2] == [
        ("validate", "600018_SH_qualitative_report.md", "qualitative"),
        ("polish", "600018_SH_qualitative_report.md", ".wxgzh"),
    ]


def test_skip_validation_allows_polish_without_validation(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_validate(*args, **kwargs):
        raise AssertionError("validation should be skipped")

    monkeypatch.setattr("wechat_report.validate_before_draft", fail_validate)

    main([str(report_path), "--qualitative-polish", "--skip-validation", "--dry-run"])


def test_qualitative_polish_rejects_turtle_and_valuation_reports(tmp_path):
    turtle_path = tmp_path / "600018_SH_turtle_report.md"
    turtle_path.write_text(VALID_TURTLE, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(turtle_path), "--qualitative-polish", "--dry-run"])

    assert "--qualitative-polish only supports qualitative reports" in str(exc.value)


def test_qualitative_polish_rejects_valuation_reports(tmp_path):
    valuation_path = tmp_path / "600018_SH_valuation_report.md"
    valuation_path.write_text(VALID_VALUATION, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(valuation_path), "--qualitative-polish", "--dry-run"])

    assert "--qualitative-polish only supports qualitative reports" in str(exc.value)


def test_qualitative_polish_rejects_type_override_for_non_qualitative_file(tmp_path):
    valuation_path = tmp_path / "600018_SH_valuation_report.md"
    valuation_path.write_text(VALID_VALUATION, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(valuation_path), "--type", "qualitative", "--qualitative-polish", "--skip-validation", "--dry-run"])

    assert "--qualitative-polish only supports qualitative reports" in str(exc.value)


def test_real_run_requires_yes(tmp_path):
    report_path = tmp_path / "600018_SH_turtle_report.md"
    report_path.write_text(VALID_TURTLE, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(report_path)])

    assert "--yes is required" in str(exc.value)


def test_real_run_executes_npx_when_yes_is_explicit(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_valuation_report.md"
    report_path.write_text(VALID_VALUATION, encoding="utf-8")
    calls = []

    def fake_run(command, check):
        calls.append((command, check))
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    main([str(report_path), "--yes", "--theme", "blue"])

    assert calls == [(
        build_wxgzh_command(
            report_path,
            output_dir=tmp_path / ".wxgzh",
            account=None,
            author=None,
            digest=None,
            theme="blue",
            cover=None,
            no_cover=False,
        ),
        True,
    )]
