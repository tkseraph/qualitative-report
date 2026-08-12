from pathlib import Path
import re

from validate_reports import (
    _has_profit_bridge_component_depth,
    _has_profit_bridge_expense_detail,
    _stock_codes,
    validate_markdown,
    validate_output_dir,
)


def test_stock_code_identity_accepts_beijing_exchange():
    assert _stock_codes("龙鑫智能（920117.BJ）") == {"920117.BJ"}


VALID_QUALITATIVE = """
# 上港集团 · 商业质量评估报告

## Business Quality Verdict
**总体评级：B+ / 中等偏强 · 稳定。** 护城河评级较强。核心优势是港口区位和规模网络，最大风险是外贸周期与吞吐量下行压力。

| 项目 | 结论 |
|---|---|
| 公司本质 | 区域枢纽港口资产 |
| 商业质量 | B+ / 中等偏强 · 稳定 |
| 护城河来源 | 区位、规模、网络 |
| 最大风险 | 外贸周期与吞吐量下行压力 |
| 周期位置 | 中性偏逆风 |
| 反证条件 | 吞吐量连续下滑或 ROE 低于资本成本 |

## Quality Snapshot
5年平均ROE、护城河评级、可持续性、管理层评价、资本强度、周期性。

## Executive Summary
公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。

### 五个核心发现
- 区位资产稀缺，支撑基础现金流。
- 规模网络真实，但不是无限定价权。
- 外贸周期是主要盈利波动来源。
- 资本开支会压制自由现金流弹性。
- 若吞吐份额下降，应重评护城河。

## 核心矛盾与反证条件
核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。
反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。

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
| 利润桥 | 利润变化主要来自毛利、销售费用、管理费用、资产减值、投资收益和非经营项，2025 ROE 约 10% | 利润质量需要穿透可持续驱动 |
| 量价成本拆解 | 吞吐量、费率和单位成本共同决定周期位置 | 周期公司不能只看收入增速 |
| 现金转化 | 经营现金流/净利润约 1.1x 与自由现金流共同验证利润含金量 | 现金弱化会降低商业质量 |
| 治理红旗 | 审计意见、关联交易、资本配置和分红纪律未见重大异常 | 治理底线暂可接受 |
| MD&A 叙事 vs 财务证据 | 管理层叙事需要被收入、利润、现金流和资本开支交叉验证 | 只报喜不报忧应降低可信度 |
| 伪优势过滤 | 区位和网络是真优势，周期高盈利不是护城河本身 | 避免把景气高点误判为结构性壁垒 |

结论：这些样板证据模块说明当前评级来自多维交叉验证，而不是单一叙事或单项指标。

### 收入质量依赖主业而非非核心扩张

chart_ready: true; chart_id: sipg-business-mix; chart_target: dimension_1; chart_type: mixed; x_axis: 业务; bar_series: 收入; line_series: 收入占比, 毛利率; unit_map: 收入=亿元, 收入占比=%, 毛利率=%

读图结论：主营收入占比越高，港口资产的基础现金流越容易被验证。

| 业务 | 收入 | 收入占比 | 毛利率 |
|---|---:|---:|---:|
| 港口装卸 | 100 亿元 | 70% | 35% |
| 物流服务 | 25 亿元 | 18% | 24% |
| 投资及其他 | 17 亿元 | 12% | 18% |

投资含义是收入质量仍主要来自港口主业，而不是非核心扩张。

### 利润桥显示毛利和费用纪律共同支撑低谷韧性

读图结论：毛利、销售费用、管理费用、减值和投资收益共同决定利润质量。

| 利润桥环节 | 当前值 | 变化方向 | 质量判断 |
|---|---:|---|---|
| 报表归母净利 | 28 亿元 | 利润表起点 | 只作为起点 |
| 毛利 | 30 亿元 | 稳定 | 主业支撑 |
| 销售费用 | 3 亿元 | 可控 | 费用纪律 |
| 管理费用 | 5 亿元 | 可控 | 费用纪律 |
| 资产减值 | 1 亿元 | 小幅 | 风险可控 |
| 投资收益 | 4 亿元 | 波动 | 需剔除观察 |
| 非经常性损益 | 1 亿元 | 一次性因素 | 需剔除 |
| 核心经营利润重算 | 23 亿元 | 计算口径：28 - 4 - 1 | 可持续利润支撑当前评级 |

投资含义是利润质量需要拆开看主业毛利、具体费用、减值和投资收益。利润桥复判必须从报表利润重算到核心经营利润，剔除非经常性损益、投资收益和一次性因素，并判断可持续利润是否支撑当前评级；计算依据必须能从表格数字复核。

### 图表三：现金质量与资本消耗决定自由现金流弹性

chart_ready: true; chart_id: sipg-cash-capex; chart_target: dimension_1; chart_type: mixed; x_axis: 年份; bar_series: OCF, FCF; line_series: OCF/净利润, Capex/D&A; unit_map: OCF=亿元, FCF=亿元, OCF/净利润=x, Capex/D&A=x

读图结论：OCF、FCF、OCF/净利润 和 Capex/D&A 放在一起，才能判断重资产现金质量。

| 指标 | 2025 | 2024 | 2023 |
|---|---:|---:|---:|
| OCF | 32 亿元 | 31 亿元 | 30 亿元 |
| FCF | 19 亿元 | 20 亿元 | 18 亿元 |
| OCF/净利润 | 1.1x | 1.1x | 1.0x |
| Capex/D&A | 1.2x | 1.2x | 1.3x |

投资含义是现金流韧性成立，但资本开支仍会约束股东可自由分配现金。

## 公司类型化证据模块
强周期或重资产公司必须把产业坐标、区域/客户结构和单位经济模型连接起来。

| 类型化问题 | 公司专属证据 | 同业/区域坐标 | 投资含义 |
|---|---|---|---|
| 强周期需求 | 吞吐量和外贸景气共同决定收入弹性 | 长三角港口群和宁波港对标 | 需求下行会先压制吞吐和费率 |
| 单位经济模型 | 吞吐量、单箱收益、单位成本和单箱毛利共同决定利润桥 | 同业费率与成本率对比 | 单位利润下滑会传导到 FCF |
| 重资产约束 | Capex/D&A 和固定资产占比约束自由现金流 | 可比港口资本开支强度对标 | 资本回报低于资本成本应降级 |

投资含义是类型化证据把产业位置、单位经济模型和现金回报连接起来，而不是只列通用框架。

## 近五年质量趋势

### 图表五：ROE 与自由现金流显示低谷质量未失速

chart_ready: true; chart_id: sipg-quality-trend; chart_target: dimension_3; chart_type: mixed; x_axis: 年份; bar_series: FCF; line_series: ROE, 毛利率, Capex/D&A; unit_map: FCF=亿元, ROE=%, 毛利率=%, Capex/D&A=x

读图结论：重资产或强周期公司必须把单年判断放回五年趋势里验证，避免把周期某一年误判为长期质量。

| 年份 | ROE | 毛利率 | 净利率 | FCF | Capex/D&A |
|---|---|---|---|---|---|
| 2021 | 11% | 32% | 18% | 25 亿元 | 1.1x |
| 2022 | 10% | 31% | 17% | 22 亿元 | 1.2x |
| 2023 | 9% | 30% | 16% | 18 亿元 | 1.3x |
| 2024 | 10% | 31% | 16% | 20 亿元 | 1.2x |
| 2025 | 10% | 30% | 15% | 19 亿元 | 1.2x |

投资含义是趋势证据能把 ROE、利润率、自由现金流和资本开支放在同一时间轴上，检验商业质量是否只是周期高点。

## 维度一：商业模式与资本特征
**结论：公司商业模式清晰，核心优势来自港口区位和吞吐网络，但资本开支和周期波动需要跟踪。**

公司赚钱公式可以压缩为五个变量：收入来源、利润驱动、资本占用、现金转化和关键反证。

| 环节 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 收入来源 | 主营港口收入约 100 亿元 | 主业质量稳定 | 非核心收入占比抬升 |
| 利润驱动 | ROE 约 10%，利润受费率和成本影响 | 利润质量中等偏稳 | 费用率异常上升 |
| 资本占用 | Capex/D&A 需持续跟踪 | 重资产约束存在 | Capex 高于经营现金流 |
| 现金转化 | OCF/净利润约 1.1x | 现金转化可接受 | 应收或自由现金流恶化 |
| 关键反证 | 吞吐、费率、现金流同步走弱 | 推翻稳定现金流判断 | 下调商业质量 |

投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。

关键结论是单位经济模型把周期公司的量价成本变化落到利润桥。

| 变量 | 当前值 | 判断 | 反证阈值 |
|---|---|---|---|
| 销量 | 吞吐量稳定 | 需求韧性尚可 | 连续两年下滑 |
| 吨价 / ASP | 单箱收益基本稳定 | 价格弹性有限 | 单箱收益下降 |
| 吨成本 / 单位成本 | 单位成本可控 | 成本优势支持利润 | 成本率明显上升 |
| 吨毛利 / 单位毛利 | 吨毛利中等 | 利润弹性受周期约束 | 吨毛利收缩 |
| 区域 / 同业坐标 | 长三角港口群与宁波港对标 | 区域竞争决定费率弹性 | 份额或费率落后同业 |

投资含义是单位经济模型能把量价成本、区域/同业坐标和现金质量连接起来，避免只看收入规模。

结论：D1 的投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。

### 本章小结
- 本章结论：商业模式清晰，收入质量稳定。
- 最重要证据：港口区位和吞吐网络支撑主业。
- 观察风险 / 重评触发：资本开支持续高于经营现金流。

## 维度二：竞争优势与护城河
**结论：护城河较强，来源于稀缺港口资源、网络规模和区域集疏运体系。**

护城河证伪表的核心，是检验结构性优势能否同时经受反向证据和同业对比。

| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 同业坐标 | 可持续 KPI |
|---|---|---|---|---|
| 上港集团 | 枢纽港口网络领先，ROE 约 10% | 费率弹性有限 | ROE、毛利率和主业现金流稳定性 | 核心港区份额 |
| 宁波港 | 长三角重要港口，盈利稳定 | 区域竞争者强 | ROE 与主业利润占比可比 | 吞吐量份额 |
| 招商港口 | 港口组合分散 | 投资收益影响大，资产结构不同 | 投资收益占比和 ROE 口径不同 | 主业利润占比 |

结论：同业对比说明优势真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。

如果高回报只来自外贸景气，那么低谷期 ROE 和现金流应同步失速；现有跨期证据不支持该假设。区位与网络优势的假设仍成立，但费率约束和同业替代限制了评级，不足以上调为强护城河。

护城河六步审讯链必须把行业地图、量化验证、护城河来源、伪优势过滤、竞争对标和可持续 KPI 放在同一节里，避免只用一个优势标签替代判断。

| 审讯环节 | 当前证据 | 反向检验 | 投资含义 |
|---|---|---|---|
| 行业地图 | 区域港口竞争格局稳定 | 新港区分流或替代通道 | 先确认市场结构 |
| 量化验证 | ROE 和毛利率仍高于弱势同业 | ROE 低于资本成本 | 超额收益必须能量化 |
| 供给侧优势 | 区位和岸线资源稀缺 | 产能扩张削弱稀缺性 | 供给侧是主要优势 |
| 需求侧弱点 | 客户仍受贸易周期影响 | 客户转换成本低 | 需求侧不是强护城河 |
| 规模边界 | 网络规模降低单位成本 | 运输半径限制全国扩张 | 规模优势有边界 |
| 伪优势过滤 | 管理和景气高点不能单独算护城河 | 周期高盈利回落 | 过滤半真优势 |
| 同业坐标 | 宁波港和招商港口作对标 | 同业 ROE 更快修复 | 相对强弱需持续复核 |
| 可持续 KPI | 核心港区份额、ROE、FCF | 指标跌破阈值 | 决定评级维持或下调 |

投资含义是上述要素只有进入连续的因果链，才足以支持护城河评级。

六步审讯按公司事实和作用机制重新归并如下。

| 步骤 | 审讯问题 | 事实与作用机制 | 当前结论 | 失效信号 |
|---|---|---|---|---|
| 1. 行业与回报 | 公司是否持续获得超额回报？ | 区域港口竞争稳定，ROE 与现金流仍有跨期支撑 | 回报真实但受周期影响 | ROE 与 FCF 连续两年低于阈值 |
| 2. 供给与规模 | 区位和规模为何难复制？ | 岸线、集疏运和吞吐网络共同降低单位成本 | 供给侧优势较强但有区域边界 | 份额与单位成本优势同步收窄 |
| 3. 需求侧 | 客户是否被锁定并接受提价？ | 客户依赖航线网络，但费率仍受贸易和竞争约束 | 需求侧粘性中等 | 降价后吞吐仍持续下降 |
| 4. 价值兑现 | 优势是否进入利润与现金？ | 主业利润、OCF 和 FCF 共同验证经营兑现 | 兑现成立，资本开支仍是约束 | OCF/净利润与 FCF 同步走弱 |
| 5. 竞争替代 | 同业能否绕开网络优势？ | 宁波港和招商港口提供区域与资产组合替代 | 非排他优势，不能给垄断溢价 | 同业 ROE 和份额连续反超 |
| 6. 持续监控 | 哪些变量决定优势继续有效？ | 份额、ROE、FCF 覆盖需求、回报和现金 | 综合护城河较强 | 任两项核心指标跌破阈值 |

这六步说明区位与网络保护现金流下限，并不自然抬高费率上限。投资含义是评级边界取决于份额、回报与自由现金流能否同时维持。

投资含义是 D2 必须先拆行业结构和优势来源，再用反证、同业和 KPI 判断护城河是否可持续。

### 图表四：同业坐标显示上港优势来自效率而非单纯规模

chart_ready: true; chart_id: sipg-peer-efficiency; chart_target: dimension_2; chart_type: mixed; x_axis: 公司; bar_series: 吞吐量; line_series: ROE, 毛利率; unit_map: 吞吐量=万箱, ROE=%, 毛利率=%

读图结论：同业坐标必须同时看规模、ROE 和毛利率，才能判断优势是效率还是单纯体量。

| 公司 | 吞吐量 | ROE | 毛利率 |
|---|---:|---:|---:|
| 上港集团 | 4850 万箱 | 10% | 30% |
| 宁波港 | 4200 万箱 | 8% | 25% |
| 招商港口 | 3300 万箱 | 7% | 22% |

投资含义是同业坐标证明优势仍有财务证据，但若同业 ROE 更快修复，需要重评相对护城河。

### 图表六：区域吞吐结构 — 主港区份额决定护城河韧性

chart_ready: true; chart_id: sipg-region-share; chart_target: dimension_2; chart_type: mixed; x_axis: 区域; bar_series: 吞吐量; line_series: 收入占比, 毛利率; unit_map: 吞吐量=万箱, 收入占比=%, 毛利率=%

读图结论：主港区吞吐占比越稳定，区位优势越能转化为现金流韧性。

| 区域 | 吞吐量 | 收入占比 | 毛利率 |
|---|---:|---:|---:|
| 核心港区 | 1200 万箱 | 70% | 35% |
| 外围港区 | 300 万箱 | 18% | 24% |
| 物流配套 | 200 万箱 | 12% | 18% |

投资含义是区域结构需要和盈利质量一起看，不能只看总吞吐规模。

### 本章小结
- 本章结论：护城河真实但受费率机制约束。
- 最重要证据：稀缺港口资源和网络规模难以复制。
- 观察风险 / 重评触发：核心港区份额持续下降。

## 维度三：外部环境
**结论：外部环境与贸易周期相关，监管风险中低，周期下行是主要风险。**

外部变量的关键，是它如何沿着需求周期 → 价格/成本 → ROE 修复空间 → 反证阈值传导到收入、利润和评级阈值。

| 外部变量 | 当前阶段 | 财务敏感性 | 预警阈值 | 重评动作 |
|---|---|---|---|---|
| 需求周期 | 中性偏逆风 | 影响吞吐量和收入弹性 | 连续两年下滑 | 下调周期位置 |
| 价格/成本 | 费率稳定但成本仍需跟踪 | 影响毛利率和单位利润 | 单箱收益下降或成本率明显上升 | 重评定价权和利润弹性 |
| ROE 修复空间 | 低谷修复但仍受重资产约束 | 决定商业质量能否从中等上修 | ROE 低于资本成本且 FCF 转弱 | 下调评级或维持观察 |

关键结论是 D3 数据驱动周期链必须用 3-5 年数据验证需求、价格、成本、毛利率、ROE 和 FCF 是否同向修复。

| 年份 | 需求/吞吐量 | 价格/单箱收益 | 成本/单位成本 | 毛利率 | ROE | FCF |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 4700 万箱 | 100 元/箱 | 65 元/箱 | 30% | 9% | 18 亿元 |
| 2024 | 4800 万箱 | 101 元/箱 | 64 元/箱 | 31% | 10% | 20 亿元 |
| 2025 | 4850 万箱 | 100 元/箱 | 65 元/箱 | 30% | 10% | 19 亿元 |

投资含义是只有需求、价格/成本、毛利率、ROE 和 FCF 在同一时间轴上同步改善，才说明周期修复能支撑评级上修。

结论：D3 的投资含义是周期属性会压制成长弹性，只有需求周期、价格/成本和 ROE 修复空间同时改善，评级上修才有基础；异常信号是吞吐量与费率同时走弱。

### 本章小结
- 本章结论：外部环境中性偏逆风。
- 最重要证据：吞吐需求受全球贸易周期影响。
- 观察风险 / 重评触发：出口链景气继续恶化。

## 维度四：管理层与治理
**结论：治理整体稳健，资本配置和分红纪律可接受，但关联交易仍需跟踪。**

管理层评价需要同时看治理红旗、资本配置和承诺兑现。

| 检查项 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 治理红旗 | 审计意见和关联交易未见重大异常 | 底线可接受 | 关联交易异常扩大 |
| 管理层/控制权 | 控股股东和管理层稳定 | 控制权风险中低 | 控制权或核心管理层异常变化 |
| 资本配置 | 分红和投资纪律稳定 | 股东回报可跟踪 | 并购回报低于资本成本 |
| 承诺兑现 | 经营叙事与吞吐趋势基本一致 | 可信度中等 | 承诺连续落空 |

投资含义是治理总表只能说明框架完整，真正决定是否降级的仍是逐项红旗排雷。

治理红旗排雷清单必须先看硬伤，再决定管理层质量是否只是加分项。

| 红旗项 | 当前证据 | 异常阈值 | 重评动作 |
|---|---|---|---|
| 审计意见 | 标准无保留 | 非标意见 | 下调治理评价 |
| 审计师变更 | 未见异常变更 | 频繁更换 | 复核会计质量 |
| 处罚 | 未见重大处罚 | 监管处罚或立案 | 提高治理折价 |
| 资金占用 | 未见非经营占用 | 控股股东占用 | 直接触发红旗 |
| 关联交易 | 披露相对稳定 | 占比异常扩大 | 复核利益输送 |
| 担保 | 未见异常担保 | 对外担保失控 | 重评或有风险 |
| 质押 | 控股权稳定 | 高比例质押 | 复核控制权风险 |
| 管理层稳定性 | 核心管理层稳定 | 频繁离任 | 降低叙事可信度 |

投资含义是治理评价先排雷，审计意见、审计师变更、处罚、资金占用、关联交易、担保、质押和管理层稳定性任一项触发，都可能让资本配置和承诺兑现失去参考意义。

关键结论是资本配置复盘表把股东回报、再投资和管理层解释放在同一口径下检验。

| 动作 | 金额 | 管理层理由 | 后续结果 | 质量评价 |
|---|---|---|---|---|
| 分红 | 约 20 亿元 | 回报股东 | 2023-2025 股东回报稳定 | 合格 |
| Capex | 约 30 亿元 | 维护港口能力 | 2023-2025 FCF 承压但未失控 | 中性 |
| 投资 | 约 10 亿元 | 补强港口网络 | 2023-2025 回报仍需跟踪 | 观察 |

投资含义是资本配置暂未破坏商业质量，但后续结果若低于资本成本应重评管理层质量；多年复盘状态显示分红兑现较稳、扩张回报仍需验证。

结论：D4 的投资含义是治理不是当前主要矛盾，但异常关联交易会直接削弱评级。

### 本章小结
- 本章结论：管理层评价合格。
- 最重要证据：资本配置和分红纪律稳定。
- 观察风险 / 重评触发：关联交易异常扩大。

## 维度五：MD&A 解读
**结论：管理层叙事与经营数据大体一致，后续需验证吞吐量与费率表现。**

管理层叙事审计表的核心，是检验财务证据、风险措辞变化和沉默信息是否一致。

| 管理层说法 | 财务验证 | 是否兑现 | 沉默信息 | 重评动作 |
|---|---|---|---|---|
| 历史指引：枢纽港韧性 | 吞吐与现金流基本匹配 | 实际兑现基本符合上一年目标 | 费率弹性解释不足 | 跟踪单箱收益 |
| 成本管控 | 成本率未见重大失控 | 部分兑现 | 单位成本拆分不足 | 跟踪成本率 |
| 新战略：资本开支 | Capex 仍影响 FCF | 新项目回报仍需验证 | 新项目回报周期披露有限 | 重评投资回报 |

投资含义是管理层叙事仍需落到费率、成本、Capex 和现金流的实际兑现。

MD&A 审讯表必须把原始说法、财务验证、实际兑现、风险措辞变化、沉默信息和下一年复核指标放在同一张表里。

| 管理层原始说法 | 财务验证 | 实际兑现 | 风险措辞变化 | 沉默信息 | 下一年复核指标 |
|---|---|---|---|---|---|
| 枢纽港韧性 | 吞吐与 OCF 基本匹配 | 基本兑现 | 外贸压力仍被提示 | 费率弹性解释不足 | 单箱收益 |
| 成本管控 | 成本率未见重大失控 | 部分兑现 | 成本压力措辞稳定 | 单位成本拆分不足 | 单位成本 |
| 新项目投资 | Capex 继续占用 FCF | 回报待验证 | 投资回报风险仍在 | 项目回报周期披露有限 | 项目 ROIC |

投资含义是 MD&A 不能只复述管理层说法，必须逐条追问财务是否验证、是否兑现、风险措辞有没有变化、哪些沉默信息会影响下一年重评。

历史目标 vs 实际兑现表可以把上一年经营计划、新战略和当年财务结果放在一起复盘。

| 年份 | 管理层目标 | 实际结果 | 偏差 | 投资含义 |
|---|---|---|---|---|
| 2023 | 稳定吞吐与现金流 | 吞吐和 OCF 基本稳定 | 基本符合 | 叙事可信度中等 |
| 2024 | 推进港口网络投资 | Capex 继续占用现金 | 回报滞后 | 跟踪投资回报 |
| 2025 | 提升运营效率 | 费用率未见失控 | 部分兑现 | 继续验证成本效率 |

投资含义是管理层叙事不是只看口号，而要看目标是否转化为收入、利润和现金流结果；2023-2025 多年兑现状态显示经营目标大体兑现，但投资回报解释仍不充分。

结论：D5 的投资含义是叙事大体可信，但异常点是管理层没有充分解释费率弹性和新增投资回报。

### 本章小结
- 本章结论：MD&A 可信度中等。
- 最重要证据：经营描述与吞吐趋势方向一致。
- 观察风险 / 重评触发：管理层叙事与现金流背离。

## 维度六：控股结构分析
**结论：集团结构需要关注，但当前不构成核心折价因素。**

D6 采用 diagnostic 诊断模式，并检查重复计价；当独立资产价值或利润占比触发阈值时升级分析。

D6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。

### SOTP 触发决策表

| 触发条件 | 当前证据 | 是否展开 | 投资含义 |
|---|---|---|---|
| 子公司利润占比超过 30% | 未见单一子公司主导利润，计算依据为子公司净利润 / 合并净利润 | 否 | 暂不做 SOTP 主判断 |
| 投资收益占比超过 20% | 投资收益需跟踪但非唯一来源，计算口径为投资收益 / 合并净利润 | 观察 | 防止利润质量被投资收益扭曲 |
| 控制权或质押异常 | 控股股东稳定，控制关系清晰，母合差异未见异常放大 | 否 | 当前不构成核心折价 |
| 子公司网络变化 | 主要子公司、关联平台和相关上市平台未见利润主导 | 否 | 暂不改变主业质量判断 |

结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。

### 本章小结
- 本章结论：控股结构不是当前核心风险。
- 最重要证据：控制关系清晰且未出现重大折价证据。
- 观察风险 / 重评触发：控制权、质押或重大子公司价值变化。

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

### 评级复判表

关键结论是复判表把支持、削弱、冲突和触发重评变量放在同一口径下，避免只重复 D1-D6 小结。

| 复判项 | 证据 | 解释 | 评级动作 |
|---|---|---|---|
| 支持当前评级的证据 | 区位、规模和 OCF 支撑基础现金流 | 护城河仍有财务证据 | 维持 |
| 削弱当前评级的证据 | 外贸周期和资本开支压制 FCF | 评级不能上调 | 观察 |
| 证据冲突的解释 | ROE 稳定但成长弹性有限 | 商业质量较强但不是强垄断 | 维持 |
| 触发重评的最小变量 | 吞吐、ROE 和 FCF 同时跌破阈值 | 需要下调至中等 | 下调 |

投资含义是当前评级可以维持，但若最小触发变量出现，应直接进入重评而不是等待年度叙事确认。

### 综合复判

综合复判：数字与叙事交叉后，当前 B+ 评级仍成立；若吞吐、ROE 和 FCF 同时跌破阈值，应从较强下调至中等。

## 深度总结
核心投资逻辑是稀缺港口资产带来稳定现金流，优势在区位、规模与网络，风险在外贸周期、资本开支和费率弹性。

## 未来观察变量
关键结论是观察变量必须连接当前证据、预警阈值和触发后的重评动作。

| 优先级 | 观察变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|---|
| P0 | 5年平均ROE | 10% | 低于资本成本 | 下调商业质量评级 |
| P0 | 吞吐量增长 | 稳定 | 连续两年下滑 | 重评周期位置 |
| P1 | 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |
| P2 | 投资收益占比 | 非主导 | 超过 20% | 复核利润质量 |

投资含义是这些分层阈值一旦触发，就需要按优先级重新评估港口资产的现金回报质量。

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
年报与 Tushare。

## 免责声明
仅供研究参考，不构成投资建议。

## 结构化参数（机器读取 / 附录）
| 参数 | 取值 |
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
| business_quality_grade | B+ |
| business_quality_label | 中等偏强 |
| rating_outlook | 稳定 |
| rating_version | 2.0 |
| sotp_mode | diagnostic |
| sotp_trigger_results | 子公司利润与投资收益均未触发完整拆分阈值 |
| sotp_data_readiness | partial |
| sotp_decision_reason | 独立分部利润与净负债披露不足，当前只做结构诊断 |
| sotp_best_feasible_analysis | 已比较子公司利润、投资收益、母合差异和控股结构 |
| sotp_double_counting_check | 已并表子公司不重复加回，关联平台只作交叉校验 |
| sotp_upgrade_trigger | 独立资产价值超过市值10%或利润贡献超过30%时升级 |
"""


def _current_contract_qualitative() -> str:
    text = VALID_QUALITATIVE.replace(
        "### 收入质量依赖主业而非非核心扩张",
        "### 图表二：收入质量依赖主业而非非核心扩张",
        1,
    ).replace(
        "## 核心矛盾与反证条件",
        "### 图表一：收入与回报保持稳定\n\n"
        "chart_ready: true; chart_id: sipg-summary-trend; chart_target: executive_summary; chart_type: mixed; x_axis: 年份; bar_series: 收入; line_series: ROE; unit_map: 收入=亿元, ROE=%\n\n"
        "读图结论：收入稳定且 ROE 维持在合理区间。\n\n"
        "| 年份 | 收入 | ROE |\n|---|---:|---:|\n| 2024 | 140 | 10 |\n| 2025 | 142 | 10 |\n\n"
        "投资含义是收入与回报没有失速，当前评级仍有基础。\n\n"
        "## 核心矛盾与反证条件",
        1,
    ).replace(
        "投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。",
        "投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。\n\n"
        "经营现金流现金桥显示，应收与存货增加属于经营资产占用，应付与合同负债增加属于客户或供应商提供的经营融资；"
        "四项变化共同解释了经营现金流，合同负债不能与资产相加称为资本占用。",
        1,
    )
    text = text.replace(
        "这六步说明区位与网络保护现金流下限，并不自然抬高费率上限。投资含义是评级边界取决于份额、回报与自由现金流能否同时维持。",
        "这六步说明区位与网络保护现金流下限，并不自然抬高费率上限。投资含义是评级边界取决于份额、回报与自由现金流能否同时维持。\n\n"
        "第一种网络效率假说认为稀缺区位和集疏运网络形成可持续成本优势；第二种周期景气假说认为回报主要来自外贸景气。"
        "现有证据保留第一种解释，但不能排除第二种；同业现金转化接近构成反例和边界，因此综合评级维持 B+。",
        1,
    )
    text = text.replace(
        "结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。",
        "结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。\n\n"
        "经济可分拆性只达到 partial：已逐项检查独立客户、产品与技术、管理及共享资源、现金流、净债务、资本开支、内部交易与资源分摊，"
        "现有证据不支持将子公司作为经济独立单元完整拆分。",
        1,
    )
    return text.replace(
        "| rating_version | 2.0 |",
        "| rating_version | 2.0 |\n"
        "| analysis_contract_version | 2.1 |\n"
        "| roe_history_years | 5 |\n"
        "| roe_available_years_avg | 10% |\n"
        "| sotp_economic_separability | partial |\n"
        "| collection_mode | 先款后货 |",
        1,
    )


def test_current_qualitative_contract_passes_enhanced_reasoning_checks():
    result = validate_markdown(
        _current_contract_qualitative(),
        "qualitative",
        quality_contract="current",
    )
    assert result.ok, result.messages


def test_current_contract_rejects_misclassified_working_capital_and_roe_history():
    text = _current_contract_qualitative().replace(
        "经营现金流现金桥显示，应收与存货增加属于经营资产占用，应付与合同负债增加属于客户或供应商提供的经营融资；四项变化共同解释了经营现金流，合同负债不能与资产相加称为资本占用。",
        "经营现金流改善只来自回款，应收、存货、应付和合同负债都计入资本占用。",
        1,
    ).replace(
        "| roe_history_years | 5 |",
        "| roe_history_years | 4 |",
        1,
    )
    result = validate_markdown(text, "qualitative", quality_contract="current")
    assert "qualitative_working_capital_cash_bridge" in result.missing
    assert "qualitative_roe_history_coverage" in result.missing


def test_current_contract_requires_order_cycle_transmission_when_classified():
    text = _current_contract_qualitative().replace(
        "| cyclicality | 强周期 |",
        "| cyclicality | 订单周期敏感 |",
        1,
    )
    result = validate_markdown(text, "qualitative", quality_contract="current")
    assert "qualitative_order_cycle_transmission" in result.missing

    text = text.replace(
        "外部变量的关键，是它如何沿着需求周期 → 价格/成本 → ROE 修复空间 → 反证阈值传导到收入、利润和评级阈值。",
        "当前阶段处于结构修复，客户资本开支 → 设备订单 → 制造交付 → 验收 → 收入 → 回款/现金构成完整订单周期传导。\n\n"
        "外部变量的关键，是它如何沿着需求周期 → 价格/成本 → ROE 修复空间 → 反证阈值传导到收入、利润和评级阈值。",
        1,
    )
    assert validate_markdown(text, "qualitative", quality_contract="current").ok




def test_profit_bridge_checks_use_detailed_profit_bridge_not_overview_module():
    md = """
# 示例公司商业质量评估报告

## 样板证据模块
| 模块 | 万泽对应证据 | 对商业质量的影响 |
|---|---|---|
| 收入质量拆分 | 收入结构证据 | 收入质量判断 |
| 利润桥 | 2025 收入 12.91 亿元、毛利约 9.26 亿元，销售/管理/研发/财务费用合计约 7.47 亿元 | 总览说明 |
| 现金转化 | OCF 和 FCF 证据 | 现金质量判断 |

## 维度一：商业模式与资本特征
重资产公司需要拆解利润桥。

### 利润桥拆解显示高毛利被费用吸收
| 项目 | 2025 金额 | 口径 | 商业质量含义 |
|---|---:|---|---|
| 营业收入 | 12.91 | 报表收入 | 基础规模 |
| 营业成本 | -3.65 | 报表营业成本 | 制造成本 |
| 毛利 | 9.26 | 收入 - 营业成本 | 主业支撑 |
| 销售费用 | -3.62 | 渠道投入 | 费用压力 |
| 管理费用 | -1.34 | 总部成本 | 费用压力 |
| 资产减值及信用减值 | -0.22 | 减值和坏账 | 资产质量压力 |
| 投资收益 | 0.00 | 非经营项 | 不构成主线 |
| 非经常性损益 | 0.22 | 一次性因素 | 需要剔除 |
| 核心经营利润重算 | 1.75 | 计算口径：归母净利 1.97 - 非经常性损益 0.22 - 投资收益 0.00 | 剔除后仍支撑当前评级 |
"""

    assert _has_profit_bridge_component_depth(md)
    assert _has_profit_bridge_expense_detail(md)


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


def test_qualitative_report_requires_fixed_first_screen_card_schema():
    text = VALID_QUALITATIVE.replace(
        "| 项目 | 结论 |",
        "| 判断项 | 结论 | 核心依据 |",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_first_screen_card_schema" in result.missing


def test_qualitative_report_requires_five_core_findings_or_equivalent():
    text = VALID_QUALITATIVE.replace(
        "\n### 五个核心发现\n- 区位资产稀缺，支撑基础现金流。\n- 规模网络真实，但不是无限定价权。\n- 外贸周期是主要盈利波动来源。\n- 资本开支会压制自由现金流弹性。\n- 若吞吐份额下降，应重评护城河。\n",
        "",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_core_findings" in result.missing


def test_qualitative_report_accepts_d_numbered_dimension_headings_and_refutation_subheading():
    text = VALID_QUALITATIVE
    replacements = {
        "## 维度一：商业模式与资本特征": "## D1. 商业模式与资本特征",
        "## 维度二：竞争优势与护城河": "## D2. 竞争优势与护城河",
        "## 维度三：外部环境": "## D3. 外部环境",
        "## 维度四：管理层与治理": "## D4. 管理层与治理",
        "## 维度五：MD&A 解读": "## D5. MD&A 解读",
        "## 维度六：控股结构分析": "## D6. 控股结构分析",
        "核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。": "### 核心矛盾\n区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n\n### 关键反证条件\n若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    result = validate_markdown(text, "qualitative")

    assert result.ok


def test_qualitative_report_accepts_reader_facing_contract_variants():
    text = VALID_QUALITATIVE.replace(
        "## Quality Snapshot\n5年平均ROE、护城河评级、可持续性、管理层评价、资本强度、周期性。",
        "## Quality Snapshot\n\n| 指标 | 结论 |\n|---|---|\n| 5年平均ROE | 10% |\n| 护城河评级 | 中 |",
    ).replace(
        "## 近五年质量趋势\n关键结论是重资产或强周期公司必须把单年判断放回五年趋势里验证，避免把周期某一年误判为长期质量。",
        "### 近五年质量趋势\n读图结论：近五年质量趋势不是稳定复利，而是从高景气回落到低谷修复。",
    ).replace(
        "| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 可持续 KPI |",
        "| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 可持续KPI |",
    ).replace(
        "关键结论是资本配置复盘表把股东回报、再投资和管理层解释放在同一口径下检验。",
        "资本配置的多年复盘状态是：分红纪律较强，Capex从高位回落，产业扩张进入验证期。",
    ).replace(
        "管理层叙事审计表的核心，是检验财务证据、风险措辞变化和沉默信息是否一致。",
        "管理层核心叙事需要用财务验证、兑现状态和沉默信息共同审计。风险措辞变化和沉默信息仍需放在一起看。",
    ).replace(
        "历史目标 vs 实际兑现表可以把上一年经营计划、新战略和当年财务结果放在一起复盘。",
        "历史目标的多年兑现状态为：方向性目标多数兑现，量化财务目标较少。",
    ).replace(
        "| 模块 | 核心证据 | 投资含义 |\n|---|---|---|\n| 收入质量拆分 | 主营港口收入约 100 亿元，非核心收入不构成主要增长来源 | 收入质量支持基础现金流判断 |\n| 利润桥 | 利润变化主要来自吞吐量、费率、成本和费用率，2025 ROE 约 10% | 利润质量需要穿透可持续驱动 |\n| 量价成本拆解 | 吞吐量、费率和单位成本共同决定周期位置 | 周期公司不能只看收入增速 |\n| 现金转化 | 经营现金流/净利润约 1.1x 与自由现金流共同验证利润含金量 | 现金弱化会降低商业质量 |\n| 治理红旗 | 审计意见、关联交易、资本配置和分红纪律未见重大异常 | 治理底线暂可接受 |\n| MD&A 叙事 vs 财务证据 | 管理层叙事需要被收入、利润、现金流和资本开支交叉验证 | 只报喜不报忧应降低可信度 |\n| 伪优势过滤 | 区位和网络是真优势，周期高盈利不是护城河本身 | 避免把景气高点误判为结构性壁垒 |",
        "| 模块 | 核心证据 | 投资含义 |\n|---|---|---|\n| 收入质量拆分 | 主营港口收入约 100 亿元，非核心收入不构成主要增长来源 | 收入质量支持基础现金流判断 |\n| 利润桥 | 利润变化主要来自吞吐量、费率、成本和费用率，2025 ROE 约 10% | 利润质量需要穿透可持续驱动 |\n| 量价成本拆解 | 吞吐量、费率和单位成本共同决定周期位置 | 周期公司不能只看收入增速 |\n| 现金转化 | 经营现金流/净利润约 1.1x 与自由现金流共同验证利润含金量 | 现金弱化会降低商业质量 |\n| 治理红旗 | 审计意见、关联交易、资本配置和分红纪律未见重大异常 | 治理底线暂可接受 |\n| 叙事验证 | 管理层叙事需要被收入、利润、现金流和资本开支交叉验证 | 只报喜不报忧应降低可信度 |\n| 优势过滤 | 区位和网络是真优势，周期高盈利不是护城河本身 | 避免把景气高点误判为结构性壁垒 |",
    ).replace(
        "## 数据来源\n年报与 Tushare。\n\n## 免责声明\n仅供研究参考，不构成投资建议。",
        "## 数据来源与免责声明\n年报与 Tushare。\n\n本报告仅供研究参考，不构成投资建议。",
    ).replace(
        "| 指标 | 结论 |",
        "| 指标 | 结论 |",
    )

    result = validate_markdown(text, "qualitative")

    assert result.ok


def test_qualitative_report_requires_strong_cycle_industry_evidence_depth():
    text = VALID_QUALITATIVE.replace(
        "## 公司类型化证据模块\n强周期或重资产公司必须把产业坐标、区域/客户结构和单位经济模型连接起来。\n\n| 类型化问题 | 公司专属证据 | 同业/区域坐标 | 投资含义 |\n|---|---|---|---|\n| 强周期需求 | 吞吐量和外贸景气共同决定收入弹性 | 长三角港口群和宁波港对标 | 需求下行会先压制吞吐和费率 |\n| 单位经济模型 | 吞吐量、单箱收益、单位成本和单箱毛利共同决定利润桥 | 同业费率与成本率对比 | 单位利润下滑会传导到 FCF |\n| 重资产约束 | Capex/D&A 和固定资产占比约束自由现金流 | 可比港口资本开支强度对标 | 资本回报低于资本成本应降级 |\n\n投资含义是类型化证据把产业位置、单位经济模型和现金回报连接起来，而不是只列通用框架。\n\n",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_strong_cycle_industry_evidence_depth" in result.missing


def test_qualitative_report_requires_cross_validation_final_reassessment():
    text = VALID_QUALITATIVE.replace(
        "### 综合复判\n\n综合复判：数字与叙事交叉后，当前 B+ 评级仍成立；若吞吐、ROE 和 FCF 同时跌破阈值，应从较强下调至中等。\n\n",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_cross_validation_final_reassessment" in result.missing


def test_qualitative_report_requires_cross_validation_reassessment_table():
    text = VALID_QUALITATIVE.replace(
        "### 评级复判表\n\n关键结论是复判表把支持、削弱、冲突和触发重评变量放在同一口径下，避免只重复 D1-D6 小结。\n\n| 复判项 | 证据 | 解释 | 评级动作 |\n|---|---|---|---|\n| 支持当前评级的证据 | 区位、规模和 OCF 支撑基础现金流 | 护城河仍有财务证据 | 维持 |\n| 削弱当前评级的证据 | 外贸周期和资本开支压制 FCF | 评级不能上调 | 观察 |\n| 证据冲突的解释 | ROE 稳定但成长弹性有限 | 商业质量较强但不是强垄断 | 维持 |\n| 触发重评的最小变量 | 吞吐、ROE 和 FCF 同时跌破阈值 | 需要下调至中等 | 下调 |\n\n投资含义是当前评级可以维持，但若最小触发变量出现，应直接进入重评而不是等待年度叙事确认。\n\n",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_cross_validation_reassessment_table" in result.missing


def test_qualitative_report_requires_profit_bridge_component_depth_for_heavy_assets():
    text = VALID_QUALITATIVE.replace(
        "利润变化主要来自毛利、销售费用、管理费用、资产减值、投资收益和非经营项，2025 ROE 约 10%",
        "利润变化主要来自吞吐量、费率、成本和费用率，2025 ROE 约 10%",
    ).replace(
        "| 利润桥环节 | 当前值 | 变化方向 | 质量判断 |\n|---|---:|---|---|\n| 报表归母净利 | 28 亿元 | 利润表起点 | 只作为起点 |\n| 毛利 | 30 亿元 | 稳定 | 主业支撑 |\n| 销售费用 | 3 亿元 | 可控 | 费用纪律 |\n| 管理费用 | 5 亿元 | 可控 | 费用纪律 |\n| 资产减值 | 1 亿元 | 小幅 | 风险可控 |\n| 投资收益 | 4 亿元 | 波动 | 需剔除观察 |\n| 非经常性损益 | 1 亿元 | 一次性因素 | 需剔除 |\n| 核心经营利润重算 | 23 亿元 | 计算口径：28 - 4 - 1 | 可持续利润支撑当前评级 |",
        "| 利润桥环节 | 当前值 | 变化方向 | 质量判断 |\n|---|---:|---|---|\n| 吞吐量 | 稳定 | 平稳 | 需跟踪 |\n| 费率 | 稳定 | 平稳 | 需跟踪 |\n| 成本 | 可控 | 平稳 | 需跟踪 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_profit_bridge_component_depth" in result.missing


def test_qualitative_report_requires_expense_bridge_detail_for_heavy_assets():
    text = VALID_QUALITATIVE.replace(
        "利润变化主要来自毛利、销售费用、管理费用、资产减值、投资收益和非经营项，2025 ROE 约 10%",
        "利润变化主要来自毛利、期间费用、资产减值、投资收益和非经营项，2025 ROE 约 10%",
    ).replace(
        "| 毛利 | 30 亿元 | 稳定 | 主业支撑 |\n| 销售费用 | 3 亿元 | 可控 | 费用纪律 |\n| 管理费用 | 5 亿元 | 可控 | 费用纪律 |\n| 资产减值 | 1 亿元 | 小幅 | 风险可控 |\n| 投资收益 | 4 亿元 | 波动 | 需剔除观察 |",
        "| 毛利 | 30 亿元 | 稳定 | 主业支撑 |\n| 期间费用 | 8 亿元 | 可控 | 费用纪律 |\n| 资产减值 | 1 亿元 | 小幅 | 风险可控 |\n| 投资收益 | 4 亿元 | 波动 | 需剔除观察 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_profit_bridge_expense_detail" in result.missing


def test_qualitative_report_requires_profit_bridge_core_operating_recast_for_heavy_assets():
    text = VALID_QUALITATIVE.replace(
        "| 核心经营利润重算 | 23 亿元 | 计算口径：28 - 4 - 1 | 可持续利润支撑当前评级 |",
        "| 报表利润 | 28 亿元 | 利润表同比改善 | 需要继续观察 |",
    ).replace(
        "利润桥复判必须从报表利润重算到核心经营利润，剔除非经常性损益、投资收益和一次性因素，并判断可持续利润是否支撑当前评级；计算依据必须能从表格数字复核。",
        "利润桥主要列示利润表项目变化，并提示后续继续观察。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_profit_bridge_core_operating_recast" in result.missing


def test_qualitative_report_requires_profit_bridge_recast_calculation_basis_for_heavy_assets():
    text = VALID_QUALITATIVE.replace(
        "| 核心经营利润重算 | 23 亿元 | 计算口径：28 - 4 - 1 | 可持续利润支撑当前评级 |",
        "| 核心经营利润重算 | 23 亿元 | 剔除投资收益和非经常性损益 | 可持续利润支撑当前评级 |",
    ).replace(
        "；计算依据必须能从表格数字复核",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_profit_bridge_recast_calculation_basis" in result.missing


def test_qualitative_report_requires_d3_cycle_transmission_to_roe_repair():
    text = VALID_QUALITATIVE.replace(
        "外部变量的关键，是它如何沿着需求周期 → 价格/成本 → ROE 修复空间 → 反证阈值传导到收入、利润和评级阈值。",
        "外部变量的关键，是它如何传导到收入、利润和评级阈值。",
    ).replace(
        "| 需求周期 | 中性偏逆风 | 影响吞吐量和收入弹性 | 连续两年下滑 | 下调周期位置 |\n| 价格/成本 | 费率稳定但成本仍需跟踪 | 影响毛利率和单位利润 | 单箱收益下降或成本率明显上升 | 重评定价权和利润弹性 |\n| ROE 修复空间 | 低谷修复但仍受重资产约束 | 决定商业质量能否从中等上修 | ROE 低于资本成本且 FCF 转弱 | 下调评级或维持观察 |",
        "| 外贸景气 | 中性偏逆风 | 影响吞吐量 | 连续两年下滑 | 下调周期位置 |\n| 费率机制 | 稳定但弹性有限 | 影响毛利率 | 单箱收益下降 | 重评定价权 |\n| 燃料与人工成本 | 成本压力可控 | 影响单位成本 | 成本率明显上升 | 重评利润弹性 |",
    ).replace(
        "结论：D3 的投资含义是周期属性会压制成长弹性，只有需求周期、价格/成本和 ROE 修复空间同时改善，评级上修才有基础；异常信号是吞吐量与费率同时走弱。",
        "结论：D3 的投资含义是周期属性会压制成长弹性，异常信号是吞吐量与费率同时走弱。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d3_cycle_roe_repair_chain" in result.missing


def test_qualitative_report_requires_d3_multi_year_cycle_data_evidence():
    text = VALID_QUALITATIVE.replace(
        "\n关键结论是 D3 数据驱动周期链必须用 3-5 年数据验证需求、价格、成本、毛利率、ROE 和 FCF 是否同向修复。\n\n| 年份 | 需求/吞吐量 | 价格/单箱收益 | 成本/单位成本 | 毛利率 | ROE | FCF |\n|---|---:|---:|---:|---:|---:|---:|\n| 2023 | 4700 万箱 | 100 元/箱 | 65 元/箱 | 30% | 9% | 18 亿元 |\n| 2024 | 4800 万箱 | 101 元/箱 | 64 元/箱 | 31% | 10% | 20 亿元 |\n| 2025 | 4850 万箱 | 100 元/箱 | 65 元/箱 | 30% | 10% | 19 亿元 |\n\n投资含义是只有需求、价格/成本、毛利率、ROE 和 FCF 在同一时间轴上同步改善，才说明周期修复能支撑评级上修。\n",
        "\n",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d3_cycle_data_evidence" in result.missing


def test_qualitative_report_requires_named_peer_or_explicit_unavailable_reason():
    text = re.sub(r"宁波港|招商港口", "同行公司", VALID_QUALITATIVE)

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_peer_comparison_named_companies" in result.missing


def test_qualitative_report_accepts_explicit_peer_unavailable_explanation():
    text = re.sub(r"宁波港|招商港口", "同业数据不可得，缺少可比公司", VALID_QUALITATIVE)

    result = validate_markdown(text, "qualitative")

    assert result.ok


def test_qualitative_report_requires_peer_comparison_dimensions_for_named_peers():
    text = VALID_QUALITATIVE.replace(
        "| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 同业坐标 | 可持续 KPI |\n"
        "|---|---|---|---|---|\n"
        "| 上港集团 | 枢纽港口网络领先，ROE 约 10% | 费率弹性有限 | ROE、毛利率和主业现金流稳定性 | 核心港区份额 |\n"
        "| 宁波港 | 长三角重要港口，盈利稳定 | 区域竞争者强 | ROE 与主业利润占比可比 | 吞吐量份额 |\n"
        "| 招商港口 | 港口组合分散 | 投资收益影响大，资产结构不同 | 投资收益占比和 ROE 口径不同 | 主业利润占比 |",
        "| 公司 | 支持护城河的证据 | 削弱护城河的反证 | 同业坐标 | 可持续 KPI |\n"
        "|---|---|---|---|---|\n"
        "| 上港集团 | 枢纽港口网络领先 | 费率弹性有限 | 同业公司 | 核心港区份额 |\n"
        "| 宁波港 | 同业公司 | 需跟踪 | 同业公司 | KPI |\n"
        "| 招商港口 | 同业公司 | 需跟踪 | 同业公司 | KPI |",
    ).replace(
        "| 公司 | 吞吐量 | ROE | 毛利率 |\n"
        "|---|---:|---:|---:|\n"
        "| 上港集团 | 4850 万箱 | 10% | 30% |\n"
        "| 宁波港 | 4200 万箱 | 8% | 25% |\n"
        "| 招商港口 | 3300 万箱 | 7% | 22% |",
        "| 公司 | 备注 |\n"
        "|---|---|\n"
        "| 上港集团 | 同业公司 |\n"
        "| 宁波港 | 同业公司 |\n"
        "| 招商港口 | 同业公司 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_peer_comparison_dimensions" in result.missing


def test_qualitative_report_requires_holding_network_depth():
    text = VALID_QUALITATIVE.replace(
        "控股股东稳定，控制关系清晰，母合差异未见异常放大",
        "控制关系清晰，母合差异未见异常放大",
    ).replace(
        "| 子公司网络变化 | 主要子公司、关联平台和相关上市平台未见利润主导 | 否 | 暂不改变主业质量判断 |\n",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_holding_network_depth" in result.missing


def test_qualitative_report_requires_chart_readouts_for_chart_friendly_tables():
    text = VALID_QUALITATIVE.replace(
        "### 图表六：区域吞吐结构 — 主港区份额决定护城河韧性",
        "### 区域吞吐结构",
    ).replace(
        "读图结论：主港区吞吐占比越稳定，区位优势越能转化为现金流韧性。",
        "",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_readout_required" in result.missing


def test_qualitative_report_requires_chart_evidence_readouts_on_profit_cash_and_peer_modules():
    text = VALID_QUALITATIVE.replace(
        "读图结论：主港区吞吐占比越稳定，区位优势越能转化为现金流韧性。",
        "主港区吞吐占比越稳定，区位优势越能转化为现金流韧性。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_readout_required" in result.missing



def test_qualitative_report_requires_chart_evidence_investment_meaning():
    text = VALID_QUALITATIVE.replace(
        "投资含义是区域结构需要和盈利质量一起看，不能只看总吞吐规模。",
        "说明：区域结构数据如上。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_evidence_investment_meaning" in result.missing



def test_qualitative_report_requires_chart_ready_metadata_for_core_chart_modules():
    text = VALID_QUALITATIVE.replace(
        "chart_ready: true; chart_id: sipg-business-mix; chart_target: dimension_1; chart_type: mixed; x_axis: 业务; bar_series: 收入; line_series: 收入占比, 毛利率; unit_map: 收入=亿元, 收入占比=%, 毛利率=%\n\n",
        "chart_ready: true; chart_id: sipg-business-mix; chart_target: dimension_1; x_axis: 业务; bar_series: 收入; line_series: 收入占比, 毛利率; unit_map: 收入=亿元, 收入占比=%, 毛利率=%\n\n",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_ready_metadata" in result.missing



def test_qualitative_report_requires_sample_level_chart_ready_count_for_heavy_assets():
    text = re.sub(r"^chart_ready: true;.*$", "", VALID_QUALITATIVE, count=3, flags=re.MULTILINE)

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_ready_sample_level_coverage" in result.missing



def test_qualitative_report_requires_sample_level_chart_archetype_coverage_for_heavy_assets():
    text = VALID_QUALITATIVE.replace("OCF/净利润", "现金转换率").replace("Capex/D&A", "资本消耗比").replace("同业坐标", "同业概览")

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_ready_archetype_coverage" in result.missing



def test_qualitative_report_rejects_chart_ready_tables_with_explanatory_columns():
    text = VALID_QUALITATIVE.replace(
        "| 业务 | 收入 | 收入占比 | 毛利率 |\n|---|---:|---:|---:|\n| 港口装卸 | 100 亿元 | 70% | 35% |\n| 物流服务 | 25 亿元 | 18% | 24% |\n| 投资及其他 | 17 亿元 | 12% | 18% |",
        "| 业务 | 收入 | 收入占比 | 毛利率 | 投资含义 |\n|---|---:|---:|---:|---|\n| 港口装卸 | 100 亿元 | 70% | 35% | 主业支撑 |\n| 物流服务 | 25 亿元 | 18% | 24% | 配套业务 |\n| 投资及其他 | 17 亿元 | 12% | 18% | 非核心 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_ready_numeric_table" in result.missing


def test_qualitative_report_requires_chart_evidence_density_above_minimum_for_heavy_assets():
    text = re.sub(
        r"### 收入质量依赖主业而非非核心扩张\n\n.*?投资含义是收入质量仍主要来自港口主业，而不是非核心扩张。\n\n",
        "",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"### 图表三：现金质量与资本消耗决定自由现金流弹性\n\n.*?投资含义是现金流韧性成立，但资本开支仍会约束股东可自由分配现金。\n",
        "",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"### 图表四：同业坐标显示上港优势来自效率而非单纯规模\n\n.*?投资含义是同业坐标证明优势仍有财务证据，但若同业 ROE 更快修复，需要重评相对护城河。\n\n",
        "",
        text,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_evidence_density" in result.missing



def test_qualitative_report_rejects_module_name_chart_titles_for_heavy_assets():
    text = VALID_QUALITATIVE.replace(
        "### 图表六：区域吞吐结构 — 主港区份额决定护城河韧性",
        "### 单位经济模型",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_title_reader_facing" in result.missing



def test_qualitative_report_rejects_readout_prefix_as_chart_title():
    text = VALID_QUALITATIVE.replace(
        "### 图表六：区域吞吐结构 — 主港区份额决定护城河韧性",
        "### 读图结论：区域吞吐结构",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_chart_title_reader_facing" in result.missing


def test_qualitative_report_rejects_instruction_like_table_prose():
    text = VALID_QUALITATIVE.replace(
        "公司赚钱公式可以压缩为五个变量：收入来源、利润驱动、资本占用、现金转化和关键反证。",
        "这张表回答公司赚钱公式：收入来源 → 利润驱动 → 资本占用 → 现金转化 → 关键反证是否共同支撑 D1 结论。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_instruction_like_prose" in result.missing



def test_qualitative_report_rejects_channel_reuse_labels_in_body():
    text = VALID_QUALITATIVE.replace(
        "公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。",
        "微信公众号摘要可复用一句话：\n公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_channel_reuse_leakage" in result.missing


def test_qualitative_report_rejects_lightweight_table_explanation_prose():
    text = VALID_QUALITATIVE.replace(
        "护城河证伪表的核心，是检验结构性优势能否同时经受反向证据和同业对比。",
        "这张证伪表的结论是：护城河需要同时经受反向证据和同业对比。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_instruction_like_prose" in result.missing


def test_qualitative_report_requires_table_context_and_investment_meaning():
    text = VALID_QUALITATIVE.replace(
        "## 维度一：商业模式与资本特征\n**结论：公司商业模式清晰，核心优势来自港口区位和吞吐网络，但资本开支和周期波动需要跟踪。**",
        "## 维度一：商业模式与资本特征\n**结论：公司商业模式清晰，核心优势来自港口区位和吞吐网络，但资本开支和周期波动需要跟踪。**\n\n| 指标 | 2025 | 判断 |\n|---|---|---|\n| 收入 | 稳定 | 支撑现金流 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_table_context" in result.missing


def test_qualitative_report_accepts_h3_table_title_with_investment_meaning():
    text = VALID_QUALITATIVE.replace(
        "管理层评价需要同时看治理红旗、资本配置和承诺兑现。\n\n| 检查项 | 当前证据 | 判断 | 风险触发 |",
        "### 治理红旗检查\n\n| 检查项 | 当前证据 | 判断 | 风险触发 |",
    )

    result = validate_markdown(text, "qualitative")

    assert result.ok


def test_qualitative_report_requires_counterevidence_in_dimensions():
    text = re.sub(
        r"观察风险 / 重评触发：[^\n]+",
        "后续跟踪：继续观察经营数据。",
        VALID_QUALITATIVE,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_dimension_counterevidence" in result.missing


def test_qualitative_report_requires_sample_evidence_modules():
    text = re.sub(
        r"\n## 样板证据模块\n.*?\n## 维度一：商业模式与资本特征",
        "\n## 维度一：商业模式与资本特征",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_sample_evidence_modules" in result.missing


def test_qualitative_report_rejects_generic_sample_evidence_modules_without_company_specific_facts():
    text = re.sub(
        r"## 样板证据模块\n.*?\n## 维度一：商业模式与资本特征",
        """## 样板证据模块
收入、利润、现金、治理与叙事需要共同支持商业质量判断。

| 模块 | 核心证据 | 投资含义 |
|---|---|---|
| 收入质量拆分 | 分析主营收入和非核心收入 | 收入质量支持基础现金流判断 |
| 利润桥 | 分析毛利、费用和非经常性损益 | 利润质量需要穿透可持续驱动 |
| 量价成本拆解 | 分析销量、价格和成本 | 周期公司不能只看收入增速 |
| 现金转化 | 分析经营现金流/净利润与自由现金流 | 现金弱化会降低商业质量 |
| 治理红旗 | 分析审计意见、关联交易和资本配置 | 治理底线需要检查 |
| MD&A 叙事 vs 财务证据 | 管理层叙事需要被收入、利润、现金流和资本开支交叉验证 | 只报喜不报忧应降低可信度 |
| 伪优势过滤 | 识别真优势、半真优势和伪优势 | 避免把景气高点误判为结构性壁垒 |

结论：这些样板证据模块说明评级来自多维交叉验证，而不是单一叙事或单项指标。

## 维度一：商业模式与资本特征""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_company_specific_evidence_modules" in result.missing


def test_qualitative_report_requires_dimension_summaries():
    text = VALID_QUALITATIVE.replace(
        "\n### 本章小结\n- 本章结论：商业模式清晰，收入质量稳定。\n- 最重要证据：港口区位和吞吐网络支撑主业。\n- 观察风险 / 重评触发：资本开支持续高于经营现金流。\n",
        "",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_dimension_summaries" in result.missing


def test_qualitative_report_requires_dimension_evidence_tables():
    text = re.sub(
        r"\n公司赚钱公式可以压缩为五个变量：收入来源、利润驱动、资本占用、现金转化和关键反证。.*?结论：D1 的投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。\n",
        "\nD1 使用段落说明收入、利润、资本消耗和现金质量。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_dimension_evidence_tables" in result.missing


def test_qualitative_report_requires_d1_business_formula_chain():
    text = re.sub(
        r"\n公司赚钱公式可以压缩为五个变量：收入来源、利润驱动、资本占用、现金转化和关键反证。.*?结论：D1 的投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。\n",
        """
收入、利润、资本消耗与现金质量需要共同支撑 D1 结论。

| 环节 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 收入拆分 | 主营港口收入约 100 亿元 | 主业质量稳定 | 非核心收入占比抬升 |
| 利润桥 | ROE 约 10%，利润受费率和成本影响 | 利润质量中等偏稳 | 费用率异常上升 |
| 资本消耗 | Capex/D&A 需持续跟踪 | 重资产约束存在 | Capex 高于经营现金流 |
| 现金质量 | OCF/净利润约 1.1x | 现金转化可接受 | 应收或自由现金流恶化 |

结论：D1 的投资含义是公司有稳定主业现金流，但异常信号是资本开支可能削弱自由现金流。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d1_business_formula" in result.missing


def test_qualitative_report_requires_d1_business_formula_as_markdown_table():
    text = re.sub(
        r"\n\| 环节 \| 当前证据 \| 判断 \| 风险触发 \|\n\|---\|---\|---\|---\|\n\| 收入来源 .*?\| 关键反证 .*?\| 下调商业质量 \|\n",
        """
- 收入来源：主营港口收入约 100 亿元，主业质量稳定，非核心收入占比抬升会触发重评。
- 利润驱动：ROE 约 10%，利润受费率和成本影响，费用率异常上升会削弱利润质量。
- 资本占用：Capex/D&A 需持续跟踪，Capex 高于经营现金流会压制自由现金流。
- 现金转化：OCF/净利润约 1.1x，应收或自由现金流恶化会下调商业质量。
- 关键反证：吞吐、费率、现金流同步走弱时推翻稳定现金流判断。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d1_business_formula" in result.missing


def test_qualitative_report_requires_d2_peer_comparison_or_unavailable_explanation():
    text = re.sub(
        r"\n护城河证伪表的核心，是检验结构性优势能否同时经受反向证据和同业对比。.*?结论：同业对比说明优势真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。\n",
        """
护城河是否来自结构性优势，不能只看周期高盈利。

| 检查项 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 区位 | 枢纽港口网络领先 | 优势较强 | 份额下降 |
| 网络 | 集疏运体系完善 | 难以复制 | 替代路线增强 |
| 费率 | 受监管和市场约束 | 定价权有限 | 单箱收益下降 |

结论：护城河真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d2_peer_comparison" in result.missing


def test_qualitative_report_requires_d2_moat_falsification_table():
    text = re.sub(
        r"\n护城河证伪表的核心，是检验结构性优势能否同时经受反向证据和同业对比。.*?结论：同业对比说明优势真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。\n",
        """
公司相对同行的护城河是否真实，需要看结构性优势和周期高盈利的区别。

| 公司 | 规模/份额 | 盈利能力 | 护城河含义 |
|---|---|---|---|
| 上港集团 | 枢纽港口网络领先 | ROE 约 10% | 区位和网络优势较强 |
| 宁波港 | 长三角重要港口 | 盈利稳定 | 区域竞争者强 |
| 招商港口 | 港口组合分散 | 投资收益影响大 | 可比但资产结构不同 |

结论：同业对比说明优势真实但不是无限定价权，异常/伪优势风险在于把周期景气误判为护城河。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d2_moat_falsification" in result.missing


def test_qualitative_report_requires_d2_moat_falsification_as_markdown_table():
    text = re.sub(
        r"\n\| 公司 \| 支持护城河的证据 \| 削弱护城河的反证 \| 同业坐标 \| 可持续 KPI \|\n\|---\|---\|---\|---\|---\|\n\| 上港集团 .*?\| 招商港口 .*?\|\n",
        """
- 上港集团：支持护城河的证据是枢纽港口网络领先，削弱护城河的反证是费率弹性有限，可持续 KPI 是核心港区份额。
- 宁波港：支持护城河的证据是长三角重要港口，削弱护城河的反证是区域竞争者强，可持续 KPI 是吞吐量份额。
- 招商港口：支持护城河的证据是港口组合分散，削弱护城河的反证是投资收益影响大，可持续 KPI 是主业利润占比。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d2_moat_falsification" in result.missing


def test_qualitative_report_requires_d2_moat_interrogation_chain():
    text = VALID_QUALITATIVE.replace(
        """
护城河六步审讯链必须把行业地图、量化验证、护城河来源、伪优势过滤、竞争对标和可持续 KPI 放在同一节里，避免只用一个优势标签替代判断。

| 审讯环节 | 当前证据 | 反向检验 | 投资含义 |
|---|---|---|---|
| 行业地图 | 区域港口竞争格局稳定 | 新港区分流或替代通道 | 先确认市场结构 |
| 量化验证 | ROE 和毛利率仍高于弱势同业 | ROE 低于资本成本 | 超额收益必须能量化 |
| 供给侧优势 | 区位和岸线资源稀缺 | 产能扩张削弱稀缺性 | 供给侧是主要优势 |
| 需求侧弱点 | 客户仍受贸易周期影响 | 客户转换成本低 | 需求侧不是强护城河 |
| 规模边界 | 网络规模降低单位成本 | 运输半径限制全国扩张 | 规模优势有边界 |
| 伪优势过滤 | 管理和景气高点不能单独算护城河 | 周期高盈利回落 | 过滤半真优势 |
| 同业坐标 | 宁波港和招商港口作对标 | 同业 ROE 更快修复 | 相对强弱需持续复核 |
| 可持续 KPI | 核心港区份额、ROE、FCF | 指标跌破阈值 | 决定评级维持或下调 |

投资含义是 D2 必须先拆行业结构和优势来源，再用反证、同业和 KPI 判断护城河是否可持续。
""",
        "\n",
    )
    text = re.sub(
        r"\n六步审讯按公司事实和作用机制重新归并如下。.*?投资含义是评级边界取决于份额、回报与自由现金流能否同时维持。\n",
        "\n",
        text,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d2_moat_interrogation_chain" in result.missing


def test_qualitative_report_requires_d5_silence_and_risk_wording_checks():
    text = VALID_QUALITATIVE.replace("风险措辞变化", "风险描述").replace("未解释清楚的问题 / 沉默信息", "后续跟踪事项").replace("管理层没有充分解释", "仍需观察")
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_silence_check" in result.missing


def test_qualitative_report_requires_d5_management_narrative_audit():
    text = re.sub(
        r"\n管理层叙事审计表的核心，是检验财务证据、风险措辞变化和沉默信息是否一致。.*?结论：D5 的投资含义是叙事大体可信，但异常点是管理层没有充分解释费率弹性和新增投资回报。\n",
        """
管理层叙事、财务证据、风险措辞变化和沉默信息需要相互印证。

| 叙事主题 | 财务验证 | 风险措辞变化 | 未解释清楚的问题 / 沉默信息 |
|---|---|---|---|
| 枢纽港韧性 | 吞吐与现金流基本匹配 | 周期压力仍需跟踪 | 费率弹性解释不足 |
| 成本管控 | 成本率未见重大失控 | 成本压力表述稳定 | 单位成本拆分不足 |
| 资本开支 | Capex 仍影响 FCF | 投资回报需验证 | 新项目回报周期披露有限 |

结论：D5 的投资含义是叙事大体可信，但异常点是管理层没有充分解释费率弹性和新增投资回报。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_management_narrative_audit" in result.missing


def test_qualitative_report_requires_d5_management_narrative_audit_as_markdown_table():
    text = re.sub(
        r"\n\| 管理层说法 \| 财务验证 \| 是否兑现 \| 沉默信息 \| 重评动作 \|\n\|---\|---\|---\|---\|---\|\n\| 历史指引：枢纽港韧性 .*?\| 新战略：资本开支 .*?\|\n",
        """
- 管理层说法：枢纽港韧性；财务验证：吞吐与现金流基本匹配；是否兑现：基本兑现；沉默信息：费率弹性解释不足；重评动作：跟踪单箱收益。
- 管理层说法：成本管控；财务验证：成本率未见重大失控；是否兑现：部分兑现；沉默信息：单位成本拆分不足；重评动作：跟踪成本率。
- 管理层说法：资本开支；财务验证：Capex 仍影响 FCF；是否兑现：仍需验证；沉默信息：新项目回报周期披露有限；重评动作：重评投资回报。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_management_narrative_audit" in result.missing


def test_qualitative_report_requires_d4_governance_capital_allocation_and_delivery():
    text = re.sub(
        r"\n## 维度四：管理层与治理\n.*?\n## 维度五：MD&A 解读",
        """
## 维度四：管理层与治理
**结论：治理整体稳健，关联交易仍需跟踪。**

治理红旗需要先排除硬伤。

| 检查项 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 治理红旗 | 审计意见和关联交易未见重大异常 | 底线可接受 | 关联交易异常扩大 |
| 关联交易 | 披露相对稳定 | 风险中低 | 交易占比异常上升 |

结论：D4 的投资含义是治理不是当前主要矛盾，但异常关联交易会直接削弱评级。

### 本章小结
- 本章结论：管理层评价合格。
- 最重要证据：治理红旗暂未触发。
- 观察风险 / 重评触发：关联交易异常扩大。

## 维度五：MD&A 解读""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d4_governance_chain" in result.missing


def test_qualitative_report_requires_d6_trigger_table():
    text = re.sub(
        r"\nD6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。.*?结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。\n",
        """
控股结构的核心问题是它是否改变商业质量判断。

| 检查项 | 当前证据 | 判断 | 投资含义 |
|---|---|---|---|
| 子公司利润占比 | 未见单一子公司主导利润 | 暂不展开 | 暂不做 SOTP 主判断 |
| 投资收益占比 | 投资收益需跟踪但非唯一来源 | 观察 | 防止利润质量被扭曲 |
| 控制权 | 控制关系清晰 | 正常 | 当前不构成核心折价 |

结论：D6 的投资含义是控股结构暂不推翻主业判断。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d6_trigger_table" in result.missing


def test_qualitative_report_requires_d6_subsidiary_investment_income_or_sotp_judgment():
    text = re.sub(
        r"\nD6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。.*?结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。\n",
        """
D6 的关键是判断集团结构是否会改变商业质量结论。

| 触发条件 | 当前证据 | 是否展开 | 投资含义 |
|---|---|---|---|
| 控制权或质押异常 | 控制关系清晰 | 否 | 当前不构成核心折价 |
| 关联交易复杂化 | 披露相对稳定 | 观察 | 防止治理折价扩大 |
| 组织层级复杂 | 集团结构可识别 | 否 | 暂不影响主业判断 |

结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是治理复杂度突然放大。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d6_subsidiary_investment_sotp" in result.missing


def test_qualitative_report_requires_company_specific_evidence_in_each_dimension():
    text = re.sub(
        r"\n## 维度三：外部环境\n.*?\n## 维度四：管理层与治理",
        """
## 维度三：外部环境
**结论：外部环境需要持续观察。**

外部变量的关键，是它如何传导到收入、利润和评级阈值。

| 外部变量 | 当前阶段 | 财务敏感性 | 预警阈值 |
|---|---|---|---|
| 行业景气 | 需要观察 | 影响收入 | 出现下滑 |
| 竞争格局 | 需要观察 | 影响利润 | 竞争加剧 |
| 成本压力 | 需要观察 | 影响费用 | 成本上升 |

结论：D3 的投资含义是外部环境会影响商业质量，异常信号是行业景气恶化。

### 本章小结
- 本章结论：外部环境需要跟踪。
- 最重要证据：行业变量会影响利润。
- 观察风险 / 重评触发：外部环境恶化。

## 维度四：管理层与治理""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_dimension_company_specific_evidence" in result.missing


def test_qualitative_report_requires_d3_cycle_sensitivity_threshold_chain():
    text = re.sub(
        r"\n## 维度三：外部环境\n.*?\n## 维度四：管理层与治理",
        """
## 维度三：外部环境
**结论：外部环境与贸易周期相关，监管风险中低。**

外部变量会影响经营表现。

| 外部变量 | 当前影响 | 判断 | 风险触发 |
|---|---|---|---|
| 外贸景气 | 影响吞吐量 | 需要观察 | 需求下滑 |
| 费率机制 | 影响毛利率 | 弹性有限 | 单箱收益下降 |
| 成本压力 | 影响单位成本 | 可控 | 成本率上升 |

结论：D3 的投资含义是外部环境会影响利润弹性。

### 本章小结
- 本章结论：外部环境中性偏逆风。
- 最重要证据：吞吐需求受全球贸易周期影响。
- 观察风险 / 重评触发：出口链景气继续恶化。

## 维度四：管理层与治理""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d3_cycle_sensitivity_threshold" in result.missing


def test_qualitative_report_requires_d4_management_or_control_right_check():
    text = re.sub(
        r"\n## 维度四：管理层与治理\n.*?\n## 维度五：MD&A 解读",
        """
## 维度四：管理层与治理
**结论：治理整体稳健，资本配置和分红纪律可接受。**

治理评价需要同时看治理红旗、资本配置和承诺兑现。

| 检查项 | 当前证据 | 判断 | 风险触发 |
|---|---|---|---|
| 治理红旗 | 审计意见和关联交易未见重大异常 | 底线可接受 | 关联交易异常扩大 |
| 信息披露 | 年报披露较完整 | 透明度可接受 | 信息披露质量下降 |
| 资本配置 | 分红和投资纪律稳定 | 股东回报可跟踪 | 并购回报低于资本成本 |
| 承诺兑现 | 经营叙事与吞吐趋势基本一致 | 可信度中等 | 承诺连续落空 |

结论：D4 的投资含义是治理不是当前主要矛盾，但异常关联交易会直接削弱评级。

### 本章小结
- 本章结论：治理评价合格。
- 最重要证据：资本配置和分红纪律稳定。
- 观察风险 / 重评触发：关联交易异常扩大。

## 维度五：MD&A 解读""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d4_management_control_check" in result.missing


def test_qualitative_report_requires_d5_history_guidance_and_new_strategy_review():
    text = re.sub(
        r"\n## 维度五：MD&A 解读\n.*?\n## 维度六：控股结构分析",
        """
## 维度五：MD&A 解读
**结论：管理层叙事与经营数据大体一致，后续需验证吞吐量与费率表现。**

管理层叙事审计表的核心，是检验财务证据、风险措辞变化和沉默信息是否一致。

| 管理层说法 | 财务验证 | 是否兑现 | 沉默信息 | 重评动作 |
|---|---|---|---|---|
| 枢纽港韧性 | 吞吐与现金流基本匹配 | 经营结果大体匹配 | 费率弹性解释不足 | 跟踪单箱收益 |
| 成本管控 | 成本率未见重大失控 | 部分兑现 | 单位成本拆分不足 | 跟踪成本率 |
| 资本开支 | Capex 仍影响 FCF | 投资回报仍需验证 | 项目回报周期披露有限 | 重评投资回报 |

结论：D5 的投资含义是叙事大体可信，但异常点是管理层没有充分解释费率弹性和新增投资回报。

### 本章小结
- 本章结论：MD&A 可信度中等。
- 最重要证据：经营描述与吞吐趋势方向一致。
- 观察风险 / 重评触发：管理层叙事与现金流背离。

## 维度六：控股结构分析""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_history_guidance_strategy_review" in result.missing


def test_qualitative_report_requires_d6_thresholds_and_calculation_basis():
    text = re.sub(
        r"\nD6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。.*?结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益、子公司利润占比或关联平台价值突然放大。\n",
        """
D6 的关键是判断子公司、投资收益或 SOTP 是否会改变商业质量结论。

| 触发条件 | 当前证据 | 是否展开 | 投资含义 |
|---|---|---|---|
| 子公司利润明显放大 | 未见单一子公司主导利润 | 否 | 暂不做 SOTP 主判断 |
| 投资收益明显放大 | 投资收益需跟踪但非唯一来源 | 观察 | 防止利润质量被投资收益扭曲 |
| 控制权或质押异常 | 控制关系清晰，母合关系未见异常放大 | 否 | 当前不构成核心折价 |

结论：D6 的投资含义是控股结构暂不推翻主业判断，异常触发条件是投资收益或子公司利润突然放大。
""",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    text = text.replace(
        "D6 采用 diagnostic 诊断模式，并检查重复计价；当独立资产价值或利润占比触发阈值时升级分析。",
        "D6 采用 diagnostic 诊断模式，并检查重复计价。",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d6_threshold_calculation_basis" in result.missing


def test_qualitative_report_requires_adaptive_research_plan():
    text = re.sub(
        r"\n## 自适应研究计划\n.*?(?=\n## 样板证据模块)",
        "",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_adaptive_research_plan" in result.missing
    assert validate_markdown(VALID_QUALITATIVE, "qualitative").ok


def test_qualitative_report_requires_cross_validation_core_conflicts_and_overlooked_signals():
    text = re.sub(
        r"\n## 交叉验证与深度分析\n.*?(?=\n## 深度总结)",
        "",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_cross_validation_research_layers" in result.missing
    assert validate_markdown(VALID_QUALITATIVE, "qualitative").ok


def test_qualitative_report_requires_adaptive_research_plan_not_conch_template_copy():
    text = re.sub(
        r"\n## 自适应研究计划\n.*?(?=\n## 样板证据模块)",
        "\n## 自适应研究计划\n轻资产软件公司的证据路径应围绕研发、渠道和海外区域展开。\n\n| 项目 | 判断 | 证据路径 | 反证重点 |\n|---|---|---|---|\n| 公司类型 | 轻资产软件公司 | 吨价、吨成本、熟料产能、碳价 | 水泥价格战 |\n| 核心质量问题 | 渠道和研发能否维持竞争优势 | 海外区域、研发效率、渠道库存 | 产品替代 |\n\n投资含义是证据必须服务核心判断。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_adaptive_research_plan" in result.missing


def test_qualitative_report_rejects_baiwan_yuan_money_unit_for_finished_report():
    text = VALID_QUALITATIVE.replace("主营港口收入约 100 亿元", "主营港口收入约 10,000 百万元")
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_money_unit_readability" in result.missing


def test_qualitative_report_rejects_merged_business_amount_cells():
    text = VALID_QUALITATIVE.replace(
        "| 收入来源 | 主营港口收入约 100 亿元 | 主业质量稳定 | 非核心收入占比抬升 |",
        "| 收入来源 | 42.5级水泥约486亿元 | 主业质量稳定 | 非核心收入占比抬升 |",
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_readable_amount_columns" in result.missing


def test_qualitative_report_requires_d4_governance_red_flag_audit_table():
    text = VALID_QUALITATIVE.replace(
        """
治理红旗排雷清单必须先看硬伤，再决定管理层质量是否只是加分项。

| 红旗项 | 当前证据 | 异常阈值 | 重评动作 |
|---|---|---|---|
| 审计意见 | 标准无保留 | 非标意见 | 下调治理评价 |
| 审计师变更 | 未见异常变更 | 频繁更换 | 复核会计质量 |
| 处罚 | 未见重大处罚 | 监管处罚或立案 | 提高治理折价 |
| 资金占用 | 未见非经营占用 | 控股股东占用 | 直接触发红旗 |
| 关联交易 | 披露相对稳定 | 占比异常扩大 | 复核利益输送 |
| 担保 | 未见异常担保 | 对外担保失控 | 重评或有风险 |
| 质押 | 控股权稳定 | 高比例质押 | 复核控制权风险 |
| 管理层稳定性 | 核心管理层稳定 | 频繁离任 | 降低叙事可信度 |

投资含义是治理评价先排雷，审计意见、审计师变更、处罚、资金占用、关联交易、担保、质押和管理层稳定性任一项触发，都可能让资本配置和承诺兑现失去参考意义。
""",
        "\n",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d4_governance_red_flag_audit" in result.missing


def test_qualitative_report_requires_d5_mda_interrogation_table():
    text = VALID_QUALITATIVE.replace(
        """
MD&A 审讯表必须把原始说法、财务验证、实际兑现、风险措辞变化、沉默信息和下一年复核指标放在同一张表里。

| 管理层原始说法 | 财务验证 | 实际兑现 | 风险措辞变化 | 沉默信息 | 下一年复核指标 |
|---|---|---|---|---|---|
| 枢纽港韧性 | 吞吐与 OCF 基本匹配 | 基本兑现 | 外贸压力仍被提示 | 费率弹性解释不足 | 单箱收益 |
| 成本管控 | 成本率未见重大失控 | 部分兑现 | 成本压力措辞稳定 | 单位成本拆分不足 | 单位成本 |
| 新项目投资 | Capex 继续占用 FCF | 回报待验证 | 投资回报风险仍在 | 项目回报周期披露有限 | 项目 ROIC |

投资含义是 MD&A 不能只复述管理层说法，必须逐条追问财务是否验证、是否兑现、风险措辞有没有变化、哪些沉默信息会影响下一年重评。
""",
        "\n",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_mda_interrogation_table" in result.missing


def test_qualitative_report_requires_d4_capital_allocation_review_table():
    text = re.sub(
        r"\n## 维度四：管理层与治理\n.*?(?=\n## 维度五：MD&A 解读)",
        "\n## 维度四：管理层与治理\n**结论：治理整体稳健。**\n\n### 本章小结\n- 本章结论：管理层评价合格。\n- 最重要证据：治理底线稳定。\n- 观察风险 / 重评触发：资本配置恶化。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d4_capital_allocation_review" in result.missing


def test_qualitative_report_requires_d5_guidance_delivery_table():
    text = re.sub(
        r"\n## 维度五：MD&A 解读\n.*?(?=\n## 维度六：控股结构分析)",
        "\n## 维度五：MD&A 解读\n**结论：MD&A 大体可信。**\n\n### 本章小结\n- 本章结论：MD&A 可信度中等。\n- 最重要证据：经营描述与财务趋势一致。\n- 观察风险 / 重评触发：叙事与现金流背离。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_d5_guidance_delivery_review" in result.missing


def test_qualitative_report_requires_limitations_and_public_clean_sources():
    without_limitations = re.sub(
        r"\n## 报告局限与数据警示\n.*?(?=\n## 数据来源)",
        "",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(without_limitations, "qualitative")

    assert not result.ok
    assert "qualitative_limitations_data_warnings" in result.missing

    with_local_path = VALID_QUALITATIVE.replace("年报与 Tushare。", "/Users/rushmind/Turtle_investment_framework/output/data_pack_market.md")
    path_result = validate_markdown(with_local_path, "qualitative")

    assert not path_result.ok
    assert "qualitative_public_output_cleanliness" in path_result.missing


def test_qualitative_report_rejects_internal_source_tags_and_workflow_prose():
    source_tagged = VALID_QUALITATIVE.replace(
        "年报与 Tushare。",
        "年报与 Tushare。[src: 年报P.21-22]",
    )
    assert "qualitative_public_output_cleanliness" in validate_markdown(
        source_tagged, "qualitative"
    ).missing

    workflow_leak = VALID_QUALITATIVE.replace(
        "年报与 Tushare。",
        "年报与 Tushare。内部工作流说明边界如下。",
    )
    assert "qualitative_public_output_cleanliness" in validate_markdown(
        workflow_leak, "qualitative"
    ).missing


def test_qualitative_report_rejects_mismatched_letter_and_text_rating():
    text = VALID_QUALITATIVE.replace(
        "| business_quality_label | 中等偏强 |",
        "| business_quality_label | 较强 |",
    )
    result = validate_markdown(text, "qualitative")
    assert "qualitative_business_quality_rating" in result.missing


def test_qualitative_report_rejects_table_only_moat_falsification():
    text = VALID_QUALITATIVE.replace(
        "如果高回报只来自外贸景气，那么低谷期 ROE 和现金流应同步失速；现有跨期证据不支持该假设。区位与网络优势的假设仍成立，但费率约束和同业替代限制了评级，不足以上调为强护城河。",
        "证据项目见表。",
    )
    result = validate_markdown(text, "qualitative")
    assert "qualitative_d2_moat_falsification" in result.missing


def test_qualitative_report_rejects_vague_sotp_mode_fields():
    text = VALID_QUALITATIVE.replace(
        "| sotp_decision_reason | 独立分部利润与净负债披露不足，当前只做结构诊断 |\n",
        "",
    )
    result = validate_markdown(text, "qualitative")
    assert "qualitative_d6_sotp_mode_contract" in result.missing


def test_qualitative_report_requires_machine_readable_appendix_fields():
    text = VALID_QUALITATIVE.replace("| management_rating | 合格 |\n", "")
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_machine_fields" in result.missing


def test_qualitative_report_rejects_parameters_before_disclaimer():
    text = VALID_QUALITATIVE.replace(
        "## 数据来源\n年报与 Tushare。\n\n## 免责声明\n仅供研究参考，不构成投资建议。\n\n## 结构化参数（机器读取 / 附录）",
        "## 结构化参数（机器读取 / 附录)\n| 参数 | 取值 |\n|---|---|\n| roe_5y_avg | 10% |\n\n## 数据来源\n年报与 Tushare。\n\n## 免责声明\n仅供研究参考，不构成投资建议。",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_parameter_appendix_order" in result.missing


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
    text = re.sub(
        r"\n## 未来观察变量\n.*?(?=\n## 数据来源)",
        "\n## 未来观察变量\n监控KPI。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing
    assert any("Future observation" in message or "观察变量" in message for message in result.messages)


def test_qualitative_report_requires_future_observation_action_language():
    text = re.sub(
        r"\n## 未来观察变量\n.*?(?=\n## 数据来源)",
        "\n## 未来观察变量\n关键结论是观察变量必须连接当前证据和预警阈值。\n\n| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 处理说明 |\n|---|---|---|---|\n| 5年平均ROE | 10% | 低于资本成本 | 记录变化 |\n| 吞吐量增长 | 稳定 | 连续两年下滑 | 记录变化 |\n| 资本开支 | 可控 | Capex/D&A 显著高于历史中位数 | 记录变化 |\n\n投资含义是这些阈值一旦触发，就需要记录变化。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_report_requires_future_observation_threshold_language_when_action_exists():
    text = re.sub(
        r"\n## 未来观察变量\n.*?(?=\n## 数据来源)",
        "\n## 未来观察变量\n关键结论是观察变量必须连接当前证据和触发后的重评动作。\n\n| 观察变量 / 监控KPI | 当前值 / 本地证据 | 触发后的重评动作 |\n|---|---|---|\n| 5年平均ROE | 10% | 下调商业质量评级 |\n| 吞吐量增长 | 稳定 | 重评周期位置 |\n| 资本开支 | 可控 | 重评现金质量 |\n\n投资含义是这些变量一旦触发，就需要重新评估港口资产的现金回报质量。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_report_requires_future_observation_current_evidence_language():
    text = re.sub(
        r"\n## 未来观察变量\n.*?(?=\n## 数据来源)",
        "\n## 未来观察变量\n关键结论是观察变量必须连接预警阈值和触发后的重评动作。\n\n| 观察变量 / 监控KPI | 预警阈值 | 触发后的重评动作 |\n|---|---|---|\n| 5年平均ROE | 低于资本成本 | 下调商业质量评级 |\n| 吞吐量增长 | 连续两年下滑 | 重评周期位置 |\n| 资本开支 | Capex/D&A 显著高于历史中位数 | 重评现金质量 |\n\n投资含义是这些阈值一旦触发，就需要重新评估港口资产的现金回报质量。\n",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "future_observation_thresholds" in result.missing


def test_qualitative_report_rejects_overlong_body_lines_for_wechat_readability():
    long_line = "这一段把收入结构、经营数据、商业含义、风险触发和重评动作全部塞在同一行里，没有分段，也没有用列表承接关键信息，读者在微信公众号窄屏里会看到一整块密集文字，因此生成链路应该要求作者拆成短段或要点；如果还继续把第二层推论、第三层风险和最终评级都放在同一行，报告就会变成审计式堆叠而不是可阅读文章；这种段落对任何公司都不是特例，应该作为通用质量门槛处理；超过极端阈值时说明报告生成已经没有遵守样板化可读性约束。"
    text = VALID_QUALITATIVE.replace(
        "**结论：公司商业模式清晰，核心优势来自港口区位和吞吐网络，但资本开支和周期波动需要跟踪。**",
        long_line,
    )

    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_readability_long_lines" in result.missing
    assert any("readability" in message.lower() or "微信" in message for message in result.messages)


def test_qualitative_first_screen_requires_advantage_and_risk():
    text = VALID_QUALITATIVE.replace(
        "**总体评级：B+ / 中等偏强 · 稳定。** 护城河评级较强。核心优势是港口区位和规模网络，最大风险是外贸周期与吞吐量下行压力。",
        "**总体评级：B+ / 中等偏强 · 稳定。** 公司经营稳健。",
    ).replace(
        "公司具备区位和规模优势，但仍受全球贸易周期影响。核心判断是港口资产质量较强，主要约束是吞吐量和费率弹性有限。",
        "公司经营稳健，资产质量较好。",
    ).replace(
        "| 护城河来源 | 区位、规模、网络 |",
        "| 业务描述 | 港口运营 |",
    ).replace(
        "| 最大风险 | 外贸周期与吞吐量下行压力 |",
        "| 当前状态 | 经营稳健 |",
    ).replace(
        "核心矛盾：区位和规模优势支持稳定现金流，但外贸周期会限制成长弹性。\n反证条件：若吞吐量连续下滑、ROE 低于资本成本或核心港区份额下降，应重评护城河评级。",
        "核心矛盾：港口运营支持稳定现金流。\n反证条件：若港区份额下降，应复核护城河评级。",
    )
    result = validate_markdown(text, "qualitative")

    assert not result.ok
    assert "qualitative_first_screen_balance" in result.missing
    assert any("first-screen" in message.lower() for message in result.messages)


def test_strong_cycle_qualitative_report_requires_unit_economics_model():
    strong_cycle = VALID_QUALITATIVE.replace(
        "| 吨价 / ASP | 单箱收益基本稳定 | 价格弹性有限 | 单箱收益下降 |\n",
        "",
    ).replace(
        "| 吨毛利 / 单位毛利 | 吨毛利中等 | 利润弹性受周期约束 | 吨毛利收缩 |\n",
        "",
    ).replace(
        "| 单位经济模型 | 吞吐量、单箱收益、单位成本和单箱毛利共同决定利润桥 | 同业费率与成本率对比 | 单位利润下滑会传导到 FCF |\n",
        "| 单位经济模型 | 吞吐量和单位成本共同决定利润桥 | 同业费率与成本率对比 | 单位利润下滑会传导到 FCF |\n",
    )
    result = validate_markdown(strong_cycle, "qualitative")

    assert not result.ok
    assert "qualitative_strong_cycle_unit_economics" in result.missing


def test_future_observations_require_priority_tiers():
    without_priority = VALID_QUALITATIVE.replace(
        "| 优先级 | 观察变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |",
        "| 观察变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |",
    ).replace(
        "|---|---|---|---|---|",
        "|---|---|---|---|",
        1,
    ).replace("| P0 | 5年平均ROE", "| 5年平均ROE").replace(
        "| P0 | 吞吐量增长",
        "| 吞吐量增长",
    ).replace(
        "| P1 | 资本开支",
        "| 资本开支",
    ).replace(
        "| P2 | 投资收益占比",
        "| 投资收益占比",
    )
    result = validate_markdown(without_priority, "qualitative")

    assert not result.ok
    assert "future_observation_priority_tiers" in result.missing


def test_strong_cycle_or_heavy_asset_qualitative_report_requires_five_year_trend_evidence():
    without_trend = re.sub(
        r"\n## 近五年质量趋势\n.*?(?=\n## 维度一：商业模式与资本特征)",
        "",
        VALID_QUALITATIVE,
        flags=re.DOTALL,
    )
    result = validate_markdown(without_trend, "qualitative")

    assert not result.ok
    assert "qualitative_multi_year_trend_evidence" in result.missing


def test_d4_d5_reviews_require_multi_year_delivery_status():
    without_multi_year_status = VALID_QUALITATIVE.replace("2023-2025 ", "").replace(
        "；多年复盘状态显示分红兑现较稳、扩张回报仍需验证",
        "",
    ).replace(
        "；2023-2025 多年兑现状态显示经营目标大体兑现，但投资回报解释仍不充分",
        "",
    )
    result = validate_markdown(without_multi_year_status, "qualitative")

    assert not result.ok
    assert "qualitative_d4_d5_multi_year_review" in result.missing


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
