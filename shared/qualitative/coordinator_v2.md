# 定性分析模块 — 协调器 v2

> **角色**：你是项目经理。职责：(1) 验证输入；(2) 加载数据；(3) 启动定性分析；(4) 交付完整报告。
>
> **架构变更 (v2)**：PDF-first 数据流。年报 PDF 直接载入 context，不经过中间格式化步骤。
> Tushare 数据仅作为历史序列补充。

---

## 输入解析

| 输入项 | 示例 | 必需？ |
|--------|------|--------|
| 股票代码或名称 | `600690` / `海尔智家` / `0001.HK` / `AAPL` | 必需 |
| 年报 PDF | 本地文件路径 或 URL | 可选（有则跳过 WebSearch） |

**解析规则**：
1. 从用户消息中提取股票代码/名称
2. 若用户提供了 PDF 链接/路径 → 下载到 `{output_dir}/annual_report.pdf`
3. 代码格式化：A股 → `XXXXXX.SH/SZ/BJ`；港股 → `XXXXX.HK`；美股 → `AAPL.US`

---

## 执行流程

```
┌──────────────────────────────────────────────┐
│  Step 1：数据采集（并行）                       │
│                                                │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ 1A Tushare数据    │  │ 1B PDF 加载      │   │
│  │ → data_pack.md    │  │ → context 直接读取│   │
│  └──────────────────┘  └──────────────────┘   │
└──────────┬─────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Step 2 + Step 1C（可并行）                    │
│                                                │
│  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Step 2:           │  │ Step 1C:          │   │
│  │ 6维度定性分析      │  │ PDF附注提取       │   │
│  │ → qualitative_    │  │ → data_pack_      │   │
│  │   report.md       │  │   report.md       │   │
│  └──────────────────┘  └──────────────────┘   │
└──────────┬─────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Step 3：HTML 仪表盘报告（可选）               │
│  report_to_html.py → {code_market}_qualitative_report.html │
└──────────────────────────────────────────────┘
```

---

## Step 1 详细指令

### 1A：Tushare 数据采集

```bash
mkdir -p {output_dir}
python3 scripts/tushare_collector.py --code {ts_code} --output {output_dir}/data_pack_market.md
```

### 1A2：确定性预算（1A 完成后）

```bash
python3 scripts/quality_control.py \
  --input {output_dir}/data_pack_market.md \
  --output {output_dir}/computed_metrics.md
```

`computed_metrics.md` 提供 CM§1-CM§6：亿元换算、同比、多年统计与 ROE 历史覆盖、分红支付率、PE 网格和项目营运资金现金桥。成功时内部证据账本直接引用 CM 定位，禁止重复心算；输入缺失或部分 CM 跳过时允许降级，但必须展示未覆盖计算的完整算式并记录缺口，不阻断提示词准备。公开报告不得保留 `[src: ...]` 标记。

### 1B：PDF 获取与加载

**PDF 获取优先级**：
1. 用户已提供 PDF 路径/URL → 直接使用
2. 用户未提供 PDF → 使用 `/download-annual-report {stock_code}` 搜索并下载最新年报（或中报）
   - 下载目标目录：`{output_dir}/`
   - 下载失败（重试后仍失败）→ fallback 到 WebSearch（Step 1C-fallback）

**PDF 读取策略**：

1. **先读目录**（通常前 3-5 页）→ 确认 PDF 类型和章节页码
2. **判断 PDF 类型**：
   - 纯文本 PDF → 直接 Read 关键章节
   - 扫描/图片 PDF → fallback 到 `python3 scripts/pdf_preprocessor.py`
3. **按需读取关键章节**（优先级排序）：

| 优先级 | 章节 | 典型页码范围 | 分析用途 |
|--------|------|-----------|--------|
| P0 | 致股东信 | 前 5-8 页 | 战略概览、管理层风格 |
| P0 | 管理层讨论与分析 | 16-60 | D1收入质量、D3行业、D5 MD&A |
| P0 | 公司治理 | 61-85 | D4 管理层 |
| P1 | 公司简介和主要财务指标 | 10-15 | D1 基础数据 |
| P1 | 股东情况 | 101-108 | D4 股权结构 |
| P2 | 财务报告附注 | 115+ | D6 控股结构、关联交易 |

每次 Read 最多 20 页，按优先级分批读取。

**1C-fallback：WebSearch 降级（仅当 PDF 下载失败时）**：
- 使用 WebSearch 补充 §7（管理层）、§8（行业）、§10（MD&A）
- 搜索时优先获取最近完整财年数据，WebSearch 关键词中加入"年报""全年"以避免返回半年报/季报结果
- 在报告中标注数据来源为 WebSearch，可信度相应降低

### 1C-peer：行业与竞品 WebSearch 补充（按需，Step 2 前置）

当 `data_pack_market.md` 的 **§8 行业与竞争** 仍含 `待Agent WebSearch补充` 占位符，或缺少 **主要竞争对手 / 同业对比 / 竞品对标** 信息时，必须先执行 WebSearch 数据补充，再启动 qualitative 写作。

执行方式：读取 `shared/qualitative/data_collection.md`，补 §8 行业与竞争及必要的 §10 管理层讨论背景；同时生成独立的 `peer_evidence.md`，格式必须使用 `Peer Evidence / 同业证据包`。WebSearch 关键词必须包含“年报”或“全年”，竞品对标必须使用全年口径（全年 vs 全年），每项外部数据记录来源 URL、Source type 和 Confidence。不得硬编码具体样板公司或单一行业同业；同业选择必须来自目标公司的行业、业务、区域、客户结构、上市可比公司或公开披露的竞争格局。

范围必须收敛：peer set 控制在 2-4 个具名同业，指标控制在 4-6 项 WebSearch 能可靠覆盖的全年口径数据；不追求穷尽同业，不得扩展成全行业数据库。找不到统一口径就写 Evidence Gaps，不强行凑完整同业矩阵。

`peer_evidence.md` 必须做到年报原文级优先：Metric Evidence 记录 `Original wording / 原文摘录`、`Page clue / 页码线索`、`Report section / 年报章节`；同一指标必须优先使用同一口径。无法取得年报原文级证据时，在 Evidence Gaps 写明“无法取得年报原文级证据”和后续复核动作；不得用媒体摘要替代 High 证据。

`peer_evidence.md` 必须区分 High / Medium / Low 置信度：High 为年报、交易所公告、公司公告或审计财报；Medium 为行业协会、监管机构、公司官网或正式业绩发布；Low 为媒体报道、财经网站摘要或非官方数据库。低置信来源不得支撑核心评级，只能提示方向或缺口。若确实找不到可比公司或行业数据，在 `peer_evidence.md` 的 Evidence Gaps 和 `data_pack_market.md` 中显式标注“同业数据不可得 / 无可比上市公司 / 可比公司数据不可得”，不要跳过 D2。

D3 轻量外部周期证据只在强周期公司触发：可补 2-3 个外部周期变量，例如需求 / 产量、价格趋势、主要成本变量，且必须是年度或全年口径；不新增庞大的周期数据库。找不到就写缺口，不用零散月度新闻拼接长期序列。

### 1D：PDF 附注提取（仅当有 PDF 时，可与 Step 2 并行）

> 此步骤为下游策略（龟龟、烟蒂等）提供结构化附注数据，不影响定性分析。
> 定性分析 Agent 和附注提取 Agent 读取 PDF 的不同区域，可并行执行。

```
Agent(
  subagent_type = "general-purpose",
  prompt = """
  请阅读 {workspace}/strategies/turtle/phase2_PDF解析.md 中的提取清单和输出格式。

  年报 PDF 文件：{output_dir}/{pdf_filename}

  步骤：
  1. 使用 Read 工具读取 PDF 前 3-5 页，获取目录页，定位附注各章节的页码。
  2. 判断 PDF 类型（纯文本 or 扫描件）：
     - 若 Read 返回清晰的中文文字和表格 → 纯文本 PDF，继续步骤 3
     - 若 Read 返回乱码或极少文字 → 扫描件，输出标记 `PDF_TYPE=SCANNED` 后停止
  3. 按优先级从 PDF 中直接 Read 对应章节（每次最多 20 页）：
     P0: 非经常性损益明细(P13)、受限现金明细(P2)
     P1: 应收账款账龄(P3)、关联交易(P4)、或有负债与承诺(P6)
     P2: 主要控股参股公司(SUB，条件触发：仅控股公司结构)
  4. 按 phase2_PDF解析.md 的格式提取结构化数据。

  将提取结果写入：{output_dir}/data_pack_report.md
  """,
  description = "PDF附注提取(供下游策略)"
)

# 扫描件 fallback（仅当上述 Agent 返回 PDF_TYPE=SCANNED 时执行）
Bash(
  command = "python3 scripts/pdf_preprocessor.py --pdf {output_dir}/{pdf_filename} --output {output_dir}/pdf_sections.json",
  description = "PDF预处理-扫描件fallback"
)
Agent(
  prompt = """
  请阅读 {workspace}/strategies/turtle/phase2_PDF解析.md 中的完整指令。
  pdf_sections.json 文件路径：{output_dir}/pdf_sections.json
  公司名称：{company_name}
  将解析结果写入：{output_dir}/data_pack_report.md
  """,
  description = "PDF精提取-扫描件fallback"
)
```

**无 PDF 时**：跳过此步骤。下游策略在无 `data_pack_report.md` 时使用降级方案。

---

## Step 2 详细指令

### 模式 A：单 Agent 全量分析（推荐）

```
Agent(
  subagent_type = "general-purpose",
  prompt = """
  请阅读 {shared_dir}/qualitative/qualitative_assessment_v2.md 中的完整分析框架。

  同时加载以下参考文件：
    - {shared_dir}/qualitative/references/judgment_examples.md（判断锚点）
    - {shared_dir}/qualitative/references/framework_guide.md（框架定义）
    - {shared_dir}/qualitative/agents/writing_style.md（写作风格）
    - {shared_dir}/qualitative/references/writing_style_rules.md（数字先行与溯源补充规则）
    - {shared_dir}/qualitative/references/industry_metrics_lookup.md（仅查目标行业；历史经验参考，不是当期证据）
    - {shared_dir}/qualitative/references/output_schema.md（参数输出规范）
    [港股] + {shared_dir}/qualitative/references/market_rules_hk.md
    [美股] + {shared_dir}/qualitative/references/market_rules_us.md

  目标公司：{stock_code}（{company_name}）

  数据文件：
    - Tushare 数据：{output_dir}/data_pack_market.md
    - 确定性预算：{output_dir}/computed_metrics.md（若存在；CM§1-CM§6 覆盖项直接引用）
    - 同业证据包：{output_dir}/peer_evidence.md（若存在，D2 优先读取；若缺失但 §8 同业信息不足，先按 data_collection.md 生成）
    - PDF 附注结构化数据：{output_dir}/data_pack_report.md（若存在，则作为优先读取的增强输入）
    - 年报 PDF：已在 context 中加载（如有）

  按照 qualitative_assessment_v2.md 的 6 维度框架进行完整分析。
  特别注意"收入质量分解"和"交叉验证"部分；若存在 data_pack_report.md，优先引用其中的 P13/P4/P6/SUB（P3 若有则一并使用）补强 D1/D4/D6 判断。若缺失，则继续按当前主路径完成分析。
  支撑评级的数字只在内部 `qualitative_evidence.json` / `qualitative_argument_map.json` 使用 CM、DP、年报页码或外部来源定位；公开报告只保留读者可理解的来源名称、年份、页码或口径，不得出现 `[src: ...]`。这是一项辅助质量要求，不替代 shared/report_contract.json 与 scripts/validate_reports.py 的现有机器契约。
  行业速查表只可用于发现异常和提出复核问题；其约 2024-2025 年历史经验可能过时，不得直接支撑评级、阈值或当期结论。
  若 data_pack_market.md 的 §8 行业与竞争缺少主要竞争对手、同业对比或竞品对标，或仍含 `待Agent WebSearch补充`，先执行 WebSearch 数据补充（按 data_collection.md）并使用全年口径生成 peer_evidence.md，再写 D2。D2 使用 peer_evidence.md 时必须遵守 Source type 和 Confidence：High 可支撑同业表和护城河判断，Medium 只作辅助背景，Low 只能提示方向或缺口，低置信来源不得支撑核心评级。peer set 控制在 2-4 个具名同业，指标控制在 4-6 项 WebSearch 能可靠覆盖的数据；不追求穷尽同业，不得扩展成全行业数据库，找不到统一口径就写 Evidence Gaps。强周期公司的 D3 轻量外部周期证据只补 2-3 个外部周期变量，例如需求 / 产量、价格趋势、主要成本变量，且必须是年度或全年口径；不新增庞大的周期数据库，找不到就写缺口。
  最终 Markdown 必须严格保留 qualitative_assessment_v2.md 的成品报告外壳：Business Quality Verdict / 商业质量总体评级、Quality Snapshot / 质量快照、Executive Summary / 执行摘要、未来观察变量、结构化参数、数据来源与免责声明。
  证据表必须回答一个明确投资问题，并按“投资问题 → 读图结论 → 表格证据 → 投资含义”组织；每组数据必须先说明它在验证哪个判断，表后必须写清楚该组证据如何影响评级、风险或反证阈值；不得只列数据不解释含义，不得把解释性字段混入图表友好数据列；图表友好数据列只放干净数值，读法、解释、证据、影响、判断、含义必须移到表前表后文字或非图表表格，不得把金额和证据写在同一个单元格。

  将最终报告写入：{output_dir}/{code_market}_qualitative_report.md
  """,
  description = "6维度定性分析"
)
```

### 模式 B：多 Agent 并行（加速）

与 v1 的 agent_a / agent_b / agent_summary 流程类似，但：
- 每个 Agent 均接收完整 data_pack_market.md + 年报 PDF 相关章节
- 不再使用 split_data_pack.py 预分发
- Summary Agent 增加交叉验证职责

### Step 2A：数字审计（报告写盘后）

1. 运行 `scripts/report_consistency.py --report {output_dir}/{code_market}_qualitative_report.md --output {output_dir}/consistency_report.md`。退出码 1 仅表示提示性冲突，必须裁定真错误还是期间、母合或口径差异；退出码 2 表示文件错误。
2. 若运行环境支持真正独立的 Agent，可在主草稿和 CM 进入其 context 前，按 `agents/cleanroom_audit.md` 生成 `cleanroom_metrics.md`；不支持时明确跳过，不得让主写作者模拟独立性。
3. 按 `agents/numeric_audit.md` 对关键数字、CM 算式、溯源标签和一致性冲突做裁决。启发式审计为辅助层，最终硬门槛仍由现有 `shared/report_contract.json` 和 `scripts/validate_reports.py` 决定。
4. `computed_metrics.md`、`cleanroom_metrics.md`、`consistency_report.md` 和 `audit.md` 均为内部工件，不写入公开报告的数据来源路径。

---

## Step 3：HTML 仪表盘（可选 — 仅用户明确要求时执行）

**默认跳过此步骤。** 仅当用户明确要求 HTML 输出时执行（如参数含 `--html`，或提到"HTML"/"网页"/"仪表盘"）。

```bash
# 本地预览（内嵌 CSS）
python3 scripts/report_to_html.py \
  --input {output_dir}/{code_market}_qualitative_report.md \
  --output {output_dir}/{code_market}_qualitative_report.html \
  --standalone

# 网站部署（引用外部 CSS）
python3 scripts/report_to_html.py \
  --input {output_dir}/{code_market}_qualitative_report.md \
  --output ~/Projects/Teracnejiang.com/zh/stock/{slug}.html
```

---

## 异常处理

| 异常情况 | 处理方式 |
|---------|---------|
| PDF 下载失败 | 提示用户重新提供链接；fallback 到 WebSearch |
| PDF 为扫描件 | 定性分析：使用 pdf_preprocessor.py 处理；附注提取：fallback 到 pdf_preprocessor.py + Agent |
| PDF 附注提取失败 | 不影响定性分析；下游策略使用降级方案（无 data_pack_report.md） |
| Tushare Token 缺失 | 降级使用 yfinance，标注数据源 |
| PDF + Tushare 数据冲突 | 以 PDF 为准，标注差异 |

---

## 文件路径约定

```
{workspace}/
├── shared/qualitative/
│   ├── coordinator_v2.md              ← 本文件
│   ├── qualitative_assessment_v2.md   ← 分析框架 v2
│   ├── agents/writing_style.md        ← 写作风格（复用）
│   ├── agents/cleanroom_audit.md      ← 独立重算协议
│   ├── agents/numeric_audit.md        ← 数字审计协议
│   └── references/                    ← 参考文件（复用）
├── scripts/
│   ├── tushare_collector.py           ← Tushare 采集
│   ├── quality_control.py             ← CM 确定性预算
│   ├── report_consistency.py          ← 跨段数字一致性审计
│   └── report_to_html.py             ← MD→HTML
├── strategies/turtle/
│   └── phase2_PDF解析.md              ← 附注提取格式规范（Step 1C 引用）
└── output/{code}_{company}/
    ├── annual_report.pdf              ← 年报 PDF
    ├── data_pack_market.md            ← Tushare 结构化数据
    ├── data_pack_report.md            ← PDF 附注结构化数据（Step 1C 输出，供下游策略）
    ├── computed_metrics.md            ← 确定性预算（内部工件）
    ├── consistency_report.md          ← 一致性扫描（内部工件）
    ├── {code_market}_qualitative_report.md    ← 分析报告
    └── {code_market}_qualitative_report.html  ← HTML 仪表盘（可选）
```

---

*定性分析模块 v2.0 | PDF-first 协调器*
