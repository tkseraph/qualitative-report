# Qualitative Report Sample-Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade qualitative reports so generated Markdown better matches the target sample reports' first-screen clarity, section rhythm, risk/refutation framing, and WeChat readability while remaining generalizable to arbitrary A-share companies.

**Architecture:** Keep the existing qualitative pipeline intact: data collection, split, Agent A/B/C analysis, Summary Agent assembly, validation, and optional WeChat draft creation. Improve the prompts and validator at the boundaries where quality is enforced: Step 5 prompt generation, qualitative agent instructions, summary assembly schema, and finished-report validation.

**Tech Stack:** Python 3.11, pytest, Markdown prompt files, existing `scripts/validate_reports.py`, `scripts/report_schema.py`, `scripts/continue_single_stock.py`, and qualitative prompt files under `shared/qualitative/agents/`.

---

## File Structure

- Modify `tests/test_validate_reports.py`: add TDD coverage for new qualitative finished-report requirements.
- Modify `tests/test_single_stock_prompts.py`: add TDD coverage that Step 5 prompt demands sample-quality and WeChat-readable qualitative output.
- Modify `scripts/report_schema.py`: add qualitative schema requirements for core contradiction/refutation, maximum risk, and monitoring thresholds.
- Modify `scripts/validate_reports.py`: add conservative qualitative quality checks for first-screen advantage/risk, missing refutation section, and observation thresholds.
- Modify `scripts/continue_single_stock.py`: enrich Step 5 prompt text so human/agent generation is guided toward the new structure.
- Modify `shared/qualitative/agents/agent_summary.md`: upgrade final report assembly instructions and target structure.
- Modify `shared/qualitative/agents/writing_style.md`: add sample-quality and WeChat/web readability rules shared by all qualitative agents.
- Modify `shared/qualitative/agents/agent_a_d1d2.md`: strengthen D1/D2 expectations for business model essence, profit/capital/cash quality, false advantages, and refutation triggers.
- Modify `shared/qualitative/agents/agent_b_d3d4d5.md`: strengthen D3/D4/D5 expectations for cycle position, governance, capital allocation, and MD&A credibility.

Do not modify `scripts/wechat_report.py` in this pass. WeChat readability is enforced through source Markdown instructions only.

---

### Task 1: Add Validator Coverage for Qualitative Sample-Quality Requirements

**Files:**
- Modify: `tests/test_validate_reports.py`

- [ ] **Step 1: Update the valid qualitative fixture**

Replace the `VALID_QUALITATIVE` string near the top of `tests/test_validate_reports.py` with this stricter fixture:

```python
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
```

- [ ] **Step 2: Add failing tests for missing qualitative quality requirements**

Add these tests after `test_valid_qualitative_report_passes`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_validate_reports.py::test_qualitative_report_requires_core_contradiction_and_refutation_section tests/test_validate_reports.py::test_qualitative_report_requires_future_observation_thresholds tests/test_validate_reports.py::test_qualitative_first_screen_requires_advantage_and_risk -q
```

Expected: all three tests fail because `scripts/report_schema.py` and `scripts/validate_reports.py` do not yet enforce these qualitative quality rules.

---

### Task 2: Implement Qualitative Schema and Validator Quality Rules

**Files:**
- Modify: `scripts/report_schema.py`
- Modify: `scripts/validate_reports.py`
- Test: `tests/test_validate_reports.py`

- [ ] **Step 1: Add schema requirements in `scripts/report_schema.py`**

In `QUALITATIVE_REQUIREMENTS`, after the `quality snapshot` requirement and before `six dimensions`, add these three requirements:

```python
    SchemaRequirement(
        "core contradiction and refutation",
        ("核心矛盾", "反证条件", "推翻判断", "重评"),
        "First-screen section that states the core tension and what would refute or downgrade the judgment.",
    ),
    SchemaRequirement(
        "maximum risk",
        ("最大风险", "核心风险", "主要约束"),
        "First-screen risk or constraint that balances the business-quality judgment.",
    ),
    SchemaRequirement(
        "monitoring thresholds",
        ("预警阈值", "触发后的重评动作", "当前值 / 本地证据"),
        "Future observation variables with current evidence, thresholds, and re-evaluation actions.",
    ),
```

- [ ] **Step 2: Add qualitative validator helper functions in `scripts/validate_reports.py`**

After `_heading_or_line_text`, add:

```python
def _section_exists_with_terms(
    md_text: str,
    heading_keywords: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> bool:
    section_text = _section_body(md_text, heading_keywords)
    return bool(section_text) and all(term in section_text for term in required_terms)


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
```

- [ ] **Step 3: Add conservative qualitative quality checks**

In `_content_quality_issues`, inside `if report_type == "qualitative":` after the existing self-consistency check, add:

```python
        if not _section_exists_with_terms(
            md_text,
            ("核心矛盾", "反证条件"),
            ("核心矛盾", "反证"),
        ):
            issues.append((
                "core_contradiction_refutation",
                "Qualitative report must include a core contradiction / refutation section that states what would downgrade the judgment.",
            ))
        future_observation = _section_body(md_text, ("未来观察", "观察变量", "监控KPI"))
        if not future_observation or not _contains_any(future_observation, ("预警阈值", "触发后的重评动作", "重评动作")):
            issues.append((
                "future_observation_thresholds",
                "Future observation variables must include current evidence, warning thresholds, and re-evaluation actions.",
            ))
        first_screen = _first_screen_text(md_text)
        has_advantage = _contains_any(first_screen, ("优势", "护城河", "壁垒", "竞争力", "质量较强", "商业质量"))
        has_risk = _contains_any(first_screen, ("风险", "约束", "压力", "下行", "反证", "重评"))
        if not has_advantage or not has_risk:
            issues.append((
                "qualitative_first_screen_balance",
                "Qualitative first-screen sections must state both the core advantage/moat and the main risk or constraint.",
            ))
```

- [ ] **Step 4: Run focused validator tests**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_validate_reports.py -q
```

Expected: all validator tests pass.

---

### Task 3: Add Prompt Coverage for Sample-Quality Step 5 Generation

**Files:**
- Modify: `tests/test_single_stock_prompts.py`

- [ ] **Step 1: Add failing prompt tests**

After `test_step5_prompt_requires_qualitative_shell_and_validation`, add:

```python
def test_step5_prompt_requires_sample_quality_first_screen_and_refutation():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "核心矛盾与反证条件" in prompt
    assert "最大风险" in prompt
    assert "反证条件" in prompt
    assert "预警阈值" in prompt
    assert "触发后的重评动作" in prompt


def test_step5_prompt_requires_wechat_readability_constraints():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "微信公众号" in prompt
    assert "段落不要过长" in prompt
    assert "表格" in prompt
    assert "每张表" in prompt
    assert "结论句" in prompt
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_single_stock_prompts.py::test_step5_prompt_requires_sample_quality_first_screen_and_refutation tests/test_single_stock_prompts.py::test_step5_prompt_requires_wechat_readability_constraints -q
```

Expected: both tests fail because `build_step5_prompt` does not yet include these new instructions.

---

### Task 4: Update Step 5 Prompt Generation

**Files:**
- Modify: `scripts/continue_single_stock.py`
- Test: `tests/test_single_stock_prompts.py`

- [ ] **Step 1: Modify `build_step5_prompt` output text**

In `scripts/continue_single_stock.py`, locate the string returned by `build_step5_prompt`. Replace the current final shell requirement sentence:

```python
        + "必须保留成品报告外壳：Business Quality Verdict / 商业质量总体评级、Quality Snapshot / 质量快照、Executive Summary / 执行摘要、未来观察变量、数据来源与免责声明。\n"
```

with:

```python
        + "必须保留并强化成品报告外壳：Business Quality Verdict / 商业质量总体评级、Quality Snapshot / 质量快照、Executive Summary / 执行摘要、核心矛盾与反证条件、未来观察变量、数据来源与免责声明。\n"
        + "首屏必须让读者快速看懂：商业质量评级、护城河来源、最大风险、主要约束、反证条件。\n"
        + "未来观察变量必须包含：当前值 / 本地证据、预警阈值、触发后的重评动作。\n"
        + "微信公众号可读性约束：段落不要过长；表格只保留关键列；每张表必须服务一个判断并配有结论句；避免审计式数据堆叠。\n"
```

- [ ] **Step 2: Run prompt tests**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_single_stock_prompts.py -q
```

Expected: all prompt tests pass.

---

### Task 5: Update Summary Agent Assembly Instructions

**Files:**
- Modify: `shared/qualitative/agents/agent_summary.md`

- [ ] **Step 1: Replace the output structure block**

In `shared/qualitative/agents/agent_summary.md`, replace the Markdown template under `## 输出` with this structure:

````markdown
```markdown
# {公司名}（{代码}）— 商业模式与护城河定性分析

> 分析日期：{日期} | 当前股价：{股价，如可得} | 总市值：{总市值，如可得} | A股

## Business Quality Verdict / 商业质量总体评级

**总体评级：{评级 + 一句话理由}。** {用 1 段说明公司本质、护城河来源、现金质量/资本强度、最大风险。}

**护城河评级：{评级}；现金质量：{评级/判断}；治理底线：{评级/判断}。** {用 1 段说明为什么评级成立，以及什么约束不能忽略。}

## Quality Snapshot / 质量快照

| 维度 | 结论 | 关键证据 |
|---|---|---|
| 5年平均ROE | {值} | {证据} |
| 护城河评级 | {值} | {证据} |
| 资本密集度 | {值} | {证据} |
| 现金效应评级 | {值} | {证据} |
| 周期性 | {值} | {证据} |
| 管理层评级 | {值} | {证据} |
| 监管/治理风险 | {值} | {证据} |
| 控股结构适用性 | {值} | {证据} |

## Executive Summary / 执行摘要

**核心判断：{用一句话概括公司质量、优势来源和主要约束。}**

关键发现：

1. **{发现1}。** {解释商业含义。}
2. **{发现2}。** {解释商业含义。}
3. **{发现3}。** {解释商业含义。}
4. **{发现4}。** {解释商业含义。}

## 核心矛盾与反证条件

**核心矛盾：{优势为什么成立，但最大约束是什么。}**

| 当前判断 | 支撑证据 | 反证条件 / 重评触发 |
|---|---|---|
| {判断1} | {证据1} | {触发1} |
| {判断2} | {证据2} | {触发2} |
| {判断3} | {证据3} | {触发3} |

## 维度一：商业模式与资本特征
[直接复制 Agent A 输出的维度一部分；必要时只统一标题层级，不改写判断]

## 维度二：竞争优势与护城河
[直接复制 Agent A 输出的维度二部分；必要时只统一标题层级，不改写判断]

## 维度三：外部环境
[直接复制 Agent B 输出的维度三部分；必要时只统一标题层级，不改写判断]

## 维度四：管理层与治理
[直接复制 Agent B 输出的维度四部分；必要时只统一标题层级，不改写判断]

## 维度五：MD&A 解读
[直接复制 Agent B 输出的维度五部分；必要时只统一标题层级，不改写判断]

## 维度六：控股结构分析
[复制 Agent C 输出，或标注“不适用”并说明原因]

## 深度总结

{2-4 段完成闭环：核心投资逻辑、最大风险、优势与风险权衡、什么情况下需要重评。}

## 未来观察变量

| 观察变量 / 监控KPI | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|
| {KPI1} | {当前值1} | {阈值1} | {动作1} |
| {KPI2} | {当前值2} | {阈值2} | {动作2} |
| {KPI3} | {当前值3} | {阈值3} | {动作3} |

## 结构化参数

| 参数 | 取值 |
|---|---|
[合并 Agent A + Agent B + Agent C 的参数表，保留 output_schema.md 要求的下游字段]

## 数据来源

{列出 Tushare、年报、pdf_sections、data_pack_report、本地计算等来源。}

## 免责声明

仅供研究参考，不构成投资建议。报告由 AI 辅助生成，可能存在数据口径、解析和判断误差。
```
````

- [ ] **Step 2: Update key notes in the same file**

Replace the existing `## 关键注意事项` list with:

```markdown
## 关键注意事项

1. **首屏质量优先**：Business Quality Verdict、Quality Snapshot、Executive Summary、核心矛盾与反证条件必须共同回答“公司强在哪里、弱在哪里、什么会推翻判断”。
2. **复制 vs 撰写**：6 个维度的正文原则上复制 Agent A/B/C 输出；可统一标题层级和格式，但不要改变原始判断。
3. **参数合并**：从 Agent A/B/C 末尾的参数表中提取值，合并为一个完整的结构化参数表。
4. **一致性检查**：如果 Agent A 和 Agent B 对同一概念使用不同术语，在首屏和参数表中统一为 output_schema.md 定义的标准值域。
5. **D6 缺失处理**：如果 agent_c_output.md 不存在，在维度六处写“不适用（非控股结构）”，在参数表中 holding_structure=false, sotp_value_mm=null, sotp_discount_pct=null。
6. **微信公众号可读性**：避免超长段落和超宽表格；每张表必须有明确用途；摘要中的每条关键发现都应包含商业含义。
```

---

### Task 6: Update Shared Writing Style Rules

**Files:**
- Modify: `shared/qualitative/agents/writing_style.md`

- [ ] **Step 1: Append sample-quality and WeChat readability rules**

At the end of `shared/qualitative/agents/writing_style.md`, append:

```markdown

## 样板化成品感要求

8. **首屏闭环**：报告开头必须同时呈现公司本质、核心优势、最大风险、反证条件，避免只报喜或只堆事实。
9. **章节节奏**：每个大维度按“结论句 → 关键证据 → 商业含义 → 风险/触发条件”组织。
10. **表格服务判断**：表格用于业务拆分、趋势、对比和风险检查；每张表前后必须有一句解释其投资含义。
11. **事实/推论/判断分离**：先说明事实，再解释含义，最后给出判断；不要把年报原话直接当结论。
12. **伪优势过滤**：遇到高 ROE、高毛利、品牌叙事、政策补贴、管理层口号时，必须判断它是真优势、半真优势还是伪优势。

## 微信公众号 / 网页可读性要求

13. **短段落**：正文段落尽量控制在 4-6 行 Markdown 源文本以内，超长论证拆成短段或编号列表。
14. **窄表格**：优先使用 3-5 列表格；若数据很多，只保留最能支撑判断的列。
15. **关键数字突出**：关键评级、阈值、异常值和风险触发条件用粗体突出。
16. **避免审计式堆叠**：不要连续罗列大量数据而不解释含义；每组数据必须服务一个判断。
17. **摘要可复用**：Executive Summary 中至少有一句短摘要可作为微信公众号 digest 的基础。
```

---

### Task 7: Update Agent A/B Qualitative Analysis Instructions

**Files:**
- Modify: `shared/qualitative/agents/agent_a_d1d2.md`
- Modify: `shared/qualitative/agents/agent_b_d3d4d5.md`

- [ ] **Step 1: Strengthen Agent A D1 instructions**

In `shared/qualitative/agents/agent_a_d1d2.md`, under `### 维度一：商业模式与资本特征`, after the one-line conclusion line, insert:

```markdown
先给出“商业模式一句话描述”：公司如何赚钱、靠什么形成利润、最主要的资本/周期约束是什么。

本维度必须形成以下判断闭环：
- 收入质量：核心收入来源是否清晰，是否存在低质量贸易/一次性收入扩张。
- 利润质量：利润来自主营经营、周期价格、投资收益、补贴还是一次性项目。
- 资本消耗：固定资产、在建工程、Capex/D&A、自由现金流是否支持轻/重资产判断。
- 现金质量：OCF/净利润、收款模式、应收账款账龄、合同负债是否支持利润兑现。
- 反证条件：哪些数据变化会推翻当前商业模式质量判断。
```

- [ ] **Step 2: Strengthen Agent A D2 instructions**

In the same file, under `#### 2.6 可持续性与监控`, replace the existing two bullets and KPI bullet with:

```markdown
- 定价权、产业链位置、侵蚀风险。
- 人力资本依赖：优势是沉淀在系统/流程/规模中，还是依赖少数人。
- 伪优势复核：高 ROE、高毛利、品牌叙事、政策补贴、管理层口号分别是真优势、半真优势还是伪优势。
- 护城河反证条件：列出 2-3 个会导致护城河评级下调的触发条件。
- **护城河监控锚点**（3个 KPI，含当前值、警戒线、触发后的重评动作）。
```

- [ ] **Step 3: Strengthen Agent B D3/D4/D5 instructions**

In `shared/qualitative/agents/agent_b_d3d4d5.md`, under `### 维度三：外部环境`, after the one-line conclusion line, insert:

```markdown
本维度必须回答：当前外部环境是顺风、逆风还是中性？如果是周期行业，当前更接近底部、中段还是顶部？哪些外部变量最可能推翻当前判断？
```

Under `### 维度四：管理层与治理`, after the one-line conclusion line, insert:

```markdown
本维度必须把管理层评价拆成：治理底线、资本配置、关联交易/质押/审计红旗、股东回报、历史兑现度。结尾列出会导致管理层评级下调的触发条件。
```

Under `### 维度五：MD&A 解读`, after the one-line conclusion line, insert:

```markdown
本维度不要复述年报措辞。必须判断管理层叙事是否与财务数据、现金流、资本开支、行业周期和上一年表述一致；标出可验证的后续 KPI。
```

---

### Task 8: Run Focused and Regression Verification

**Files:**
- No code changes unless tests expose failures.

- [ ] **Step 1: Run focused tests**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_validate_reports.py tests/test_single_stock_prompts.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run related report tests**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests/test_wechat_report.py tests/test_build_data_pack_report.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run non-integration test suite**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python -m pytest tests -q -m "not integration"
```

Expected: all non-integration tests pass.

- [ ] **Step 4: Validate current Muyuan fresh output and document expected failure if any**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/validate_reports.py output/002714_e2e_fresh
```

Expected: This may fail if the existing Muyuan report lacks the new `核心矛盾与反证条件` section. If it fails, do not patch the report by hand unless the user asks. Record that existing reports need regeneration under the new prompt/schema.

- [ ] **Step 5: Verify generated Step 5 prompt contains new requirements**

Run:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/continue_single_stock.py --output-dir output/002714_e2e_fresh --stage step5
```

Expected: output mentions `核心矛盾与反证条件`, `最大风险`, `反证条件`, `预警阈值`, `触发后的重评动作`, and `微信公众号可读性约束`.

---

### Task 9: Cleanup and Completion Notes

**Files:**
- No required code changes.

- [ ] **Step 1: Check git status**

Run:

```bash
git status --short
```

Expected: changes include only the intended tracked files and the design/plan docs. `.superpowers/` should remain uncommitted or be cleaned/ignored after asking the user.

- [ ] **Step 2: Report completion with evidence**

Report:

- tests run and pass/fail counts;
- whether current Muyuan existing output passes or needs regeneration;
- changed files;
- no push and no PR.

Do not commit unless the user explicitly asks for a commit.
