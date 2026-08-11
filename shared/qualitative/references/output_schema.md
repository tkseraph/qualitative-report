# 定性分析结构化参数输出 Schema（v2.0）

> 定义定性分析模块输出的标准化参数。下游投资策略（龟龟、烟蒂等）通过读取该参数表获取定性结论，
> 各策略可在自己的 interface 文件中定义额外的映射规则。
>
> v2.0 更新：总体商业质量评级采用统一的“字母 / 文字”双轨体系并与护城河评级分离；
> D6 用明确的 SOTP 模式和决策字段替代含混的“暂不展开”。

---

## 参数定义

### 总体商业质量评级（报告级）

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| business_quality_grade | enum | A / A- / B+ / B / B- / C / D | 总体商业质量字母档位 |
| business_quality_label | enum | 优秀 / 较强 / 中等偏强 / 中等 / 中等偏弱 / 较弱 / 不合格 | 与字母档位一一对应的中文结论 |
| rating_outlook | enum | 正面 / 稳定 / 观察 / 负面 | 未来 12-24 个月结论变化方向，不混入评级本身 |
| rating_version | string | 2.0 | 评级体系版本 |

固定映射为：`A / 优秀`、`A- / 较强`、`B+ / 中等偏强`、`B / 中等`、
`B- / 中等偏弱`、`C / 较弱`、`D / 不合格`。展示格式为“字母 / 文字”，可在其后追加“· 展望”。
`moat_rating` 只评价护城河，不得替代总体商业质量评级。

### D1：商业模式与资本特征

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| business_model_clarity | enum | 清晰且已验证 / 清晰但未充分验证 / 模糊 | 商业模式是否可用一句话概括并经历周期验证 |
| capital_intensity | enum | capital-light / capital-hungry | 维持盈利规模的持续性资本消耗 |
| collection_mode | enum | 先款后货 / 订阅预收 / 先货后款 / 垫资回收 | 典型交易的现金流时间线 |
| cash_impact | enum | 正贡献 / 中性 / 负担 | 收款模式对现金状况的影响 |

### D2：竞争优势与护城河

**D2.1 行业地图**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| market_structure | enum | 垄断 / 寡头 / 垄断竞争 / 充分竞争 | 行业竞争格局 |
| market_cr4 | float / null | 百分比 | 前4名市场份额合计（数据可得时填写） |
| entry_barrier | enum | 高 / 中 / 低 | 行业进入壁垒综合评估 |

**D2.2 量化验证**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| roe_5y_avg | float | 百分比 | 5年平均ROE |
| moat_existence | enum | 存在 / 可能存在 / 不存在 | 基于量化数据的竞争优势存在性判断 |
| moat_evidence_strength | enum | 强证据 / 中等证据 / 弱证据 | 量化证据的强度 |

**D2.3 护城河来源（双框架）**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| moat_type | string | "[非技术] xxx + [技术] xxx" | 框架A：双层护城河描述（技术层可为"不适用"） |
| moat_framework_primary | enum | A / B | 主分析框架：A=双层(科技)，B=Greenwald(传统) |
| supply_side_rating | enum | 强 / 较强 / 中等 / 弱 / 不适用 | 框架B：供给侧优势（成本、资源、垂直整合） |
| demand_side_rating | enum | 强 / 较强 / 中等 / 弱 / 不适用 | 框架B：需求侧优势（品牌、转换成本、网络效应） |
| scale_economy_rating | enum | 强 / 较强 / 中等 / 弱 / 不适用 | 框架B：规模经济效益 |
| moat_flywheel | bool | true / false | 是否形成复合护城河飞轮 |

**D2.4 虚假优势辨析**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| false_advantages | list | [string] | 被排除的"虚假优势"列表及理由 |

**D2.5 竞争对手对比**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| competitors | list | [{name, ticker}] | 主要竞争对手列表 |
| competitor_ranking | string | 自由文本 | 目标公司 vs 对手的综合排名 |
| advantage_gap_sustainability | enum | 高 / 中 / 低 | 优势差距可持续性 |

**D2.6 可持续性与综合**

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| pricing_power | enum | 强 / 中 / 弱 | 主动提价能力 |
| human_capital_dep | enum | 系统型 / 人才型 | 竞争优势是否已沉淀为系统性能力 |
| moat_sustainability | enum | 高可持续 / 中等可持续 / 低可持续 | 护城河可持续性判断 |
| moat_rating | enum | 强 / 较强 / 中 / 弱 | 护城河综合评价 |
| moat_monitor_kpis | list | [{kpi, current, threshold}] | 未来3-5年护城河健康度跟踪指标 |

### D3：外部环境

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| cyclicality | enum | 强周期 / 弱周期 / 非周期 | 收入和盈利波动幅度 |
| cycle_position | enum | 底部 / 中段 / 顶部 / 不适用 | 当前周期位置（仅强周期适用） |
| regulatory_risk | enum | 低 / 中 / 高 | 监管与政策风险 |
| industry_keywords | list | [string] | 行业监控关键词 |

### D4：管理层与治理

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| governance_flags | list | [{flag_name: status}] | 治理风险逐项标志 |
| management_rating | enum | 优秀 / 合格 / 损害价值 / 观察期 | 管理层综合评价 |
| capital_allocation_record | string | 自由文本 | 资本配置历史简要评价 |
| related_party_risk | enum | 低 / 中 / 高 | 关联交易风险 |

### D5：MD&A 解读

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| mda_credibility | enum | 高 / 中 / 低 | MD&A 可信度 |
| mda_impact | enum | 正面 / 中性 / 负面 | MD&A 对投资判断的影响 |
| mda_forward_guidance | enum | 有量化 / 仅方向性 / 无 | 前瞻性指引质量 |
| distribution_signal | string | 自由文本 | 从 MD&A 提取的分红/回购意向摘要 |

### D6：控股结构（条件触发）

| 参数 | 类型 | 值域 | 说明 |
|------|------|------|------|
| holding_structure | bool | true / false | 是否适用控股结构分析 |
| sotp_mode | enum | not_applicable / diagnostic / listed_asset_bridge / full | D6 实际采用的分析深度 |
| sotp_trigger_results | string / object | 逐项触发结论 | 子公司利润、投资收益、母合差异、非经常项、分部价值等触发测试 |
| sotp_data_readiness | enum | sufficient / partial / insufficient / not_applicable | 完整 SOTP 所需数据的完备程度 |
| sotp_decision_reason | string | 明确结论 | 为什么选择当前模式，禁止只写“暂不展开” |
| sotp_best_feasible_analysis | string | 明确结论 | 现有证据下已经完成的最优可行分析 |
| sotp_double_counting_check | string | 明确结论 | 共享渠道、品牌、供应链、净现金和关联持股的重复计价检查 |
| sotp_upgrade_trigger | string | 可观测阈值 | 何种数据或业务变化会升级到更深模式 |
| sotp_value_mm | float / null | 百万元 | SOTP 估值（不适用时为 null） |
| sotp_discount_pct | float / null | 百分比 | 控股折价率（不适用时为 null） |

---

## 使用说明

### 独立运行模式
参数表附在完整分析报告末尾，供阅读者快速定位结论。

### 被策略调用模式
下游策略通过读取参数表获取定性结论，不需要解析报告正文。各策略在自己的 interface 文件中定义映射规则，例如：

- **龟龟策略**：`strategies/turtle/references/factor_interface.md` 定义 output_schema → 龟龟因子参数的映射
- **烟蒂策略**：`strategies/cigarbutt/references/cigarbutt_interface.md` 定义 output_schema → 烟蒂支柱评分的映射

### 版本兼容
- Schema 版本号：v2.0
- v1.1 → v2.0 变更：新增总体商业质量评级、评级展望、评级版本，以及 D6 SOTP 模式与决策字段；总体评级与 `moat_rating` 分离
- v1.0 → v1.1 变更：D2 新增 market_cr4, entry_barrier, roe_5y_avg, moat_existence, moat_evidence_strength, moat_framework_primary, supply_side_rating, demand_side_rating, scale_economy_rating, false_advantages, competitor_ranking, advantage_gap_sustainability, moat_sustainability, moat_monitor_kpis；moat_rating 值域扩展为 强/较强/中/弱
- 新增参数向后兼容（下游策略忽略未知参数）
- 删除/改名参数需同步更新所有策略的 interface 文件

---

*通用定性分析模块 v1.1 | 结构化参数输出 Schema*
