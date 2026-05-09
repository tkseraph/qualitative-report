# Qualitative Report WeChat Polish Design

## Goal

Continue upgrading qualitative reports so they not only pass stricter finished-report validation, but also read more like publish-ready sample reports in WeChat Official Account drafts.

The implementation must remain generalizable to arbitrary A-share companies. Muyuan Foods (`002714`) is a calibration case only; no company-specific wording, thresholds, or rules should be hard-coded.

## Context

The current qualitative upgrade already improved the report shell:

- `Business Quality Verdict / 商业质量总体评级`
- `Quality Snapshot / 质量快照`
- `Executive Summary / 执行摘要`
- `核心矛盾与反证条件`
- D1-D6 qualitative dimensions
- `深度总结`
- `未来观察变量`
- `结构化参数`
- `数据来源`
- `免责声明`

The regenerated Muyuan report now passes the upgraded validator and has stronger judgment density. The remaining gap versus the target samples is mostly presentation rhythm:

- first screen still feels dense rather than card-like;
- some middle sections still read like analyst working notes;
- tables can be wide for mobile reading;
- structured parameters are useful for downstream machines but should not dominate human reading;
- WeChat draft output needs a safer digest and more predictable source Markdown.

The user selected a two-step path:

1. lightweight Markdown-source optimization;
2. WeChat-first polish / preview layer, with HTML used as local preview support rather than a website project.

## Non-goals

- Do not build or deploy a website.
- Do not publish, mass-send, or schedule WeChat articles.
- Do not store WeChat credentials.
- Do not rewrite the whole qualitative pipeline.
- Do not hard-code Muyuan-specific conclusions or thresholds.
- Do not remove structured parameters required by turtle and valuation.
- Do not make all presentation preferences hard validator failures; prefer warnings or prompt constraints where false positives are likely.

## Design Part 1: Markdown Source Optimization

### 1. First-screen summary card

Qualitative reports should include a compact first-screen card immediately after `Business Quality Verdict` or as part of it.

The card should answer:

- company essence;
- business quality rating;
- moat source;
- maximum risk / core constraint;
- current cycle or external position when relevant;
- refutation / re-evaluation condition.

The card should use a narrow table with at most three columns, for example:

| 项目 | 结论 |
|---|---|
| 公司本质 | {一句话} |
| 商业质量 | {评级 + 理由} |
| 护城河来源 | {来源} |
| 最大风险 | {风险} |
| 周期位置 | {位置 / 不适用} |
| 反证条件 | {触发条件} |

This is a structural pattern, not a company-specific template. It should work for banks, manufacturing, consumer, cyclical, agriculture, and asset-heavy companies.

### 2. Section summaries

Each D1-D6 section should end with a short `本章小结` block when evidence is substantial.

The block should contain two to three bullets:

- `本章结论`;
- `最重要证据`;
- `观察风险 / 重评触发`.

This lets WeChat readers skim the report without reading every paragraph.

### 3. Narrow-table discipline

Prompt rules should require:

- regular body tables should prefer three to four columns;
- five or more columns are allowed only when the table would lose meaning if split;
- wide financial tables should be converted into `判断 / 关键证据 / 含义` style where possible;
- every table should be preceded or followed by a sentence that explains what judgment it supports.

This should be enforced through prompt and warning-level checks, not hard validator failures in the first implementation.

### 4. Structured parameters as appendix

`结构化参数` must remain in the Markdown and keep downstream fields for turtle and valuation.

However, the report should explicitly frame it as appendix / machine-readable metadata. It should appear after the human-facing conclusion, future observation variables, data sources, and disclaimer where feasible, or be labeled clearly as:

`结构化参数（机器读取 / 附录）`

The WeChat polish layer can fold or visually de-emphasize it, while the canonical Markdown remains complete.

### 5. Article-like deep summary

`深度总结` should be structured as a readable ending:

1. company essence;
2. why the advantage is real;
3. maximum risk;
4. what would trigger re-evaluation.

This improves sample-like rhythm without changing analytical substance.

## Design Part 2: WeChat-first Polish and Preview Layer

### 1. Qualitative polish mode in `wechat_report.py`

Add an optional qualitative-only polish mode:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/002714_e2e_fresh \
  --type qualitative \
  --qualitative-polish \
  --dry-run
```

Behavior:

1. Validate the original report first unless `--skip-validation` is explicitly provided.
2. Create a polished Markdown copy under `.wxgzh/`, for example:
   - `.wxgzh/002714_SZ_qualitative_report.polished.md`
3. Use the polished Markdown file for the downstream `wxgzh` command.
4. Never modify the original canonical report.
5. Apply only to `--type qualitative` or explicit qualitative report files.
6. Refuse or ignore `--qualitative-polish` for turtle and valuation unless future designs explicitly support them.

### 2. Automatic safe digest

For qualitative reports, the CLI should support automatic digest generation when the user does not provide `--digest`.

Digest source priority:

1. first sentence of `Executive Summary / 执行摘要` core judgment;
2. first sentence of `Business Quality Verdict`;
3. title-based fallback.

Digest should be trimmed to a conservative WeChat-safe length to avoid `description size out of limit`.

The existing user-validated workflow already found that WeChat rejects oversized descriptions, so this is a practical default for qualitative draft creation.

### 3. Polished Markdown transforms

The first implementation should keep transforms conservative and reversible:

- add or preserve a short first-screen digest block if absent;
- mark `结构化参数` as appendix / machine-readable;
- add comments or warning output for very wide tables rather than rewriting complex financial tables blindly;
- optionally convert simple wide tables when they match a known safe pattern;
- keep data values and analytical judgments unchanged.

The polish layer should be presentation-only. It must not change ratings, risks, thresholds, or investment judgment.

### 4. Local HTML preview

Add optional preview generation:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/wechat_report.py output/002714_e2e_fresh \
  --type qualitative \
  --qualitative-polish \
  --preview-html \
  --dry-run
```

Outputs:

- polished Markdown under `.wxgzh/`;
- preview HTML under `.wxgzh/`, for example:
  - `.wxgzh/002714_SZ_qualitative_report.preview.html`

The preview should help inspect:

- whether the first screen reads like cards;
- whether tables are too wide;
- whether structured parameters are de-emphasized;
- whether section summaries are present;
- whether mobile-width reading is acceptable.

This preview is not a deployed website. It can reuse `scripts/report_to_html.py` and `shared/qualitative/templates/dashboard.html`, but should not force website deployment assumptions.

### 5. `report_to_html.py` support for the upgraded qualitative structure

`report_to_html.py` already parses qualitative reports, but should recognize the new sections more explicitly:

- `Business Quality Verdict`;
- `Quality Snapshot`;
- `核心矛盾与反证条件`;
- `未来观察变量`;
- `结构化参数` / `结构化参数（机器读取 / 附录）`;
- `深度总结`.

The template should render:

- verdict and first-screen card near the top;
- core contradiction as a callout or card;
- future observation variables as a monitoring table;
- structured parameters inside `<details>`.

This supports local preview and future website work without making website work part of this project.

## Data Flow

Normal qualitative generation remains:

1. collect / load local data;
2. generate canonical qualitative Markdown;
3. validate canonical report;
4. optionally create WeChat draft.

New optional WeChat flow:

1. discover qualitative report;
2. validate original report;
3. generate polished Markdown copy under `.wxgzh/`;
4. optionally generate preview HTML under `.wxgzh/`;
5. dry-run or execute `wxgzh` with the polished Markdown;
6. real draft creation still requires explicit `--yes`.

## Testing Strategy

### Markdown prompt tests

Modify or add tests around Step 5 / qualitative prompt generation to verify that generation instructions require:

- first-screen summary card;
- D1-D6 section summaries;
- narrow-table discipline;
- structured parameters as appendix / machine-readable;
- article-like deep summary.

### WeChat polish tests

Add tests for `scripts/wechat_report.py` covering:

- `--qualitative-polish` creates a polished Markdown copy under `.wxgzh/`;
- original report is not modified;
- automatic digest is generated and length-limited when `--digest` is absent;
- explicit `--digest` still wins;
- polish is allowed for qualitative and rejected or ignored for turtle/valuation;
- `--dry-run` still does not call `subprocess.run`;
- validation still runs before polish unless explicitly skipped;
- polished command uses the polished Markdown path.

### HTML preview tests

Add tests for preview behavior:

- `--preview-html` with `--qualitative-polish` writes `.preview.html`;
- preview generation does not require network;
- preview includes core qualitative sections if the input report has them;
- missing template or invalid input produces a clear local error.

### Regression tests

Existing tests for:

- `validate_reports.py`;
- `test_single_stock_prompts.py`;
- `test_wechat_report.py`;
- `test_build_data_pack_report.py`;
- non-integration test suite

should keep passing.

## Acceptance Criteria

- Qualitative prompt instructions require card-like first screen, section summaries, narrow tables, appendix-style structured parameters, and article-like conclusion.
- Canonical qualitative Markdown remains complete and validator-compatible.
- WeChat polish mode creates a derived Markdown file without changing the original report.
- Qualitative drafts can use a safe auto digest by default.
- Local preview HTML can be generated for qualitative reports without publishing or deploying anything.
- Turtle and valuation WeChat behavior is not changed except for shared code paths that remain tested.
- The implementation is general across A-share companies and contains no Muyuan-specific rules.
