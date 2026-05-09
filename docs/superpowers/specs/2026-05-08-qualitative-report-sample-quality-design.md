# Qualitative Report Sample-Quality Upgrade Design

## Goal

Upgrade qualitative reports from structurally complete Markdown outputs into publish-ready research reports that approach the quality, hierarchy, and finished-report feel of the target samples while remaining generalizable to arbitrary A-share companies.

The design uses Muyuan Foods (`002714`) as the first calibration case because local annual-report data and existing outputs are available, but the implementation must not hard-code Muyuan-specific conclusions, thresholds, or wording.

## Context

The project's long-term goal is stable generation of three finished A-share reports:

1. `qualitative`: business quality / moat / six-dimension qualitative report.
2. `turtle`: Turtle strategy report.
3. `valuation`: valuation report.

The qualitative report is upstream of the other two reports, so improving its judgment density and structure should improve downstream turtle and valuation quality.

The target samples are:

- `https://terancejiang.com/zh/stock/yealink-300628-qualitative`
- `https://terancejiang.com/zh/stock/muyuan-002714-qualitative`
- `https://terancejiang.com/zh/stock/conch-cement-600585-qualitative`

The user selected all three improvement priorities:

- A. stronger first-screen finished-report feel.
- B. better section reading rhythm and judgment flow.
- C. better WeChat Official Account readability.

## Current State

Relevant local reports:

- `output/002714_e2e_fresh/002714_SZ_qualitative_report.md`
- `output/002714_acceptance/002714_SZ_qualitative_report.md`

Observed strengths in the current fresh report:

- It already has a top verdict, quality snapshot, executive summary, six dimensions, deep summary, future observation variables, and structured parameters.
- It contains strong evidence density: business mix, cash flow, capital intensity, cycle position, governance, related-party transactions, and D6 structure.
- It passes the current finished-report validator.

Observed gaps relative to the target samples:

- The report can feel more like an audit-style long document than a publish-ready research article.
- First-screen hierarchy is good but not yet strong enough: the core contradiction, maximum risk, and refutation conditions are not consistently explicit.
- Some sections provide large amounts of evidence without always turning the evidence into a tight judgment loop.
- WeChat reading can suffer from long paragraphs and wide tables.
- Current validation mostly confirms required sections exist; it does not strongly enforce sample-like report quality.

## Target Quality Standard

A good qualitative report should let a reader understand the following within the first 30 seconds:

- business quality rating;
- moat rating and moat source;
- company essence in one sentence;
- maximum risk or core constraint;
- current cycle / external environment position where relevant;
- what would falsify or downgrade the current judgment.

The whole report should follow this pattern:

1. `Business Quality Verdict / 商业质量总体评级`
2. `Quality Snapshot / 质量快照`
3. `Executive Summary / 执行摘要`
4. `核心矛盾与反证条件`
5. Six dimensions:
   - D1: business model and capital characteristics;
   - D2: competitive advantage and moat;
   - D3: external environment;
   - D4: management and governance;
   - D5: MD&A interpretation;
   - D6: holding structure analysis when applicable.
6. `深度总结`
7. `未来观察变量`
8. `结构化参数`
9. `数据来源`
10. `免责声明`

Each major analytical section should use this rhythm:

1. one conclusion-first sentence;
2. 2-4 pieces of key evidence;
3. explanation of what the evidence means;
4. risk / trigger / refutation condition where applicable.

Tables should support a judgment, not merely list data. Each table should be followed or preceded by a short interpretation.

## Proposed Architecture

### 1. Upgrade the Summary Agent as the main assembly point

Primary file:

- `shared/qualitative/agents/agent_summary.md`

Rationale:

The Summary Agent controls final report assembly, first-screen structure, executive summary, deep summary, and parameter consolidation. It is the highest-leverage place to enforce finished-report feel without rewriting lower-level data extraction.

Changes to design:

- Replace the older `执行摘要 -> six dimensions -> 总结与投资启示` structure with the target report structure above.
- Require `Business Quality Verdict` to include:
  - overall business quality grade;
  - moat rating;
  - cash quality / capital intensity signal;
  - maximum risk or constraint;
  - one-sentence company essence.
- Require `Quality Snapshot` to include 6-9 rows:
  - 5-year average ROE;
  - moat rating;
  - capital intensity;
  - cash impact;
  - cyclicality;
  - cycle position when applicable;
  - management rating;
  - related-party / governance risk;
  - D6 applicability when relevant.
- Require `Executive Summary` to contain 4-6 numbered key findings, each with a business implication, not just a fact.
- Add `核心矛盾与反证条件` after the executive summary.
- Rename / align `总结与投资启示` into `深度总结` to match current validator and target sample style.
- Require `未来观察变量` to include `当前值 / 本地证据`, `预警阈值`, and `触发后的重评动作`.

### 2. Strengthen shared writing style

Primary file:

- `shared/qualitative/agents/writing_style.md`

Changes to design:

- Add WeChat / web readability rules:
  - avoid paragraphs longer than roughly 4-6 Chinese lines in Markdown source;
  - prefer short numbered findings for first-screen summary;
  - avoid overly wide tables; use 4-5 columns where possible;
  - every table must serve an explicit judgment;
  - do not repeat the same evidence in multiple dimensions unless it changes interpretation;
  - distinguish facts, interpretation, and judgment.
- Add sample-quality rules:
  - each section starts with a conclusion sentence;
  - each section ends or contains a risk / trigger condition where meaningful;
  - avoid generic positive adjectives without evidence;
  - explicitly flag when data is unavailable rather than filling with narrative.

### 3. Improve Agent A output expectations

Primary file:

- `shared/qualitative/agents/agent_a_d1d2.md`

Changes to design:

- D1 should include:
  - one-sentence business model;
  - revenue quality;
  - profit quality;
  - capital consumption;
  - cash collection / cash quality;
  - business model refutation or deterioration triggers.
- D2 should include:
  - industry map;
  - quantitative validation;
  - moat source;
  - false-advantage filter;
  - competitor comparison when evidence exists;
  - moat sustainability;
  - moat refutation conditions.

### 4. Improve Agent B output expectations

Primary file:

- `shared/qualitative/agents/agent_b_d3d4d5.md`

Changes to design:

- D3 should identify cycle position and the most important external variables.
- D4 should include governance red flags, related-party risk, capital allocation, and shareholder-return quality.
- D5 should evaluate MD&A credibility instead of restating management language.
- D4/D5 should explicitly ask: what would change the management/governance judgment?

### 5. Strengthen finished-report schema and validator

Primary files:

- `scripts/report_schema.py`
- `scripts/validate_reports.py`

Schema additions for qualitative reports:

- `core contradiction / refutation conditions`: keywords like `核心矛盾`, `反证条件`, `推翻判断`, `重评`.
- `maximum risk`: keywords like `最大风险`, `核心风险`, `主要约束`.
- `monitoring thresholds`: keywords like `预警阈值`, `触发后的重评动作`, `当前值`.
- Retain existing requirements for verdict, snapshot, executive summary, six dimensions, deep summary, structured parameters, data sources, and disclaimer.

Validator additions:

- Reject qualitative reports where the first-screen sections do not mention both an advantage and a risk.
- Reject future-observation sections that do not include threshold / trigger language.
- Reject missing or generic `核心矛盾与反证条件` sections.
- Keep rules conservative to avoid false positives on valid companies whose structure differs by industry.

Possible validator warnings, not hard failures in the first implementation:

- very long paragraphs;
- very wide tables;
- repeated generic section bodies.

These can become hard failures later if real usage shows they are stable.

### 6. WeChat readability as source-Markdown constraints

Primary files:

- `shared/qualitative/agents/agent_summary.md`
- `shared/qualitative/agents/writing_style.md`
- optional future: `scripts/wechat_report.py`

First implementation should not rewrite the `wxgzh` pipeline. It should make the Markdown itself more WeChat-friendly:

- shorter executive summary findings;
- stable heading hierarchy;
- fewer ultra-wide tables;
- shorter paragraphs;
- explicit short summary language that can be reused as `--digest` later.

A later separate project can add a dedicated WeChat formatting pass if source-level constraints are insufficient.

## Data Flow

Current flow remains intact:

1. market / report data collection;
2. data splitting;
3. Agent A and B analysis;
4. optional Agent C;
5. Summary Agent assembly;
6. validator;
7. optional WeChat draft creation.

The main change is that Agent A/B/C produce more judgment-ready sections, and Summary Agent assembles them into a stronger first-screen and closing structure.

## Testing Strategy

### Focused prompt/schema tests

Modify or add tests in:

- `tests/test_single_stock_prompts.py`
- `tests/test_validate_reports.py`

Expected coverage:

- Step 5 prompt requires:
  - `Business Quality Verdict`;
  - `Quality Snapshot`;
  - `核心矛盾与反证条件`;
  - `未来观察变量`;
  - data sources and disclaimer;
  - WeChat/web readability constraints.
- Qualitative validator fails if:
  - core contradiction / refutation section is missing;
  - future observation variables lack threshold / trigger language;
  - first-screen conclusion lacks either moat/advantage or risk language;
  - data sources or disclaimer are missing.

### Regression tests

Existing validator tests for turtle and valuation must keep passing.

Existing fixed acceptance sample tests should not be expanded proactively. Muyuan can be used as a local calibration and smoke target, not as a new permanent matrix expansion unless the user later requests it.

### Manual smoke

Use Muyuan fresh output as the first manual comparison target:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/validate_reports.py output/002714_e2e_fresh
```

After implementation, regenerate or refresh a qualitative report prompt for Muyuan and inspect whether the prompt now demands the target structure.

## Non-goals

- Do not hard-code target sample wording.
- Do not hard-code Muyuan-specific details.
- Do not expand the fixed sample matrix.
- Do not build a new website.
- Do not formally publish to WeChat.
- Do not rewrite all report rendering / HTML generation in this pass.
- Do not weaken downstream structured parameters needed by turtle and valuation.

## Acceptance Criteria

- Qualitative generation instructions explicitly require sample-like first-screen structure, section rhythm, risk/refutation framing, and observation thresholds.
- Validator enforces the new qualitative structure conservatively.
- Existing qualitative/turtle/valuation validation tests continue to pass.
- Muyuan remains a calibration case, not a special-case implementation.
- Generated Markdown remains suitable for downstream turtle and valuation use.
- Source Markdown is more suitable for WeChat draft creation: shorter first-screen summary, clearer headings, and less table sprawl.
