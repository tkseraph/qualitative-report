# Qualitative Report WeChat Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a general, A-share-compatible qualitative report polish path that improves Markdown source rhythm, creates WeChat-ready derived Markdown, and generates local preview HTML without modifying canonical reports.

**Architecture:** Keep the canonical qualitative report as the source of truth. Strengthen generation prompts for future reports, then add a presentation-only polish layer in `scripts/wechat_report.py` that writes `.wxgzh/*.polished.md`, derives a safe digest, and optionally calls a reusable `report_to_html.py` renderer for `.preview.html`. Extend the existing qualitative HTML parser/template to recognize the upgraded qualitative sections instead of creating a website project.

**Tech Stack:** Python standard library, pytest, existing `markdown` and `jinja2` dependencies, existing CLI scripts under `scripts/`, existing qualitative templates under `shared/qualitative/`.

**Local constraints:** Use `/Users/rushmind/Turtle_investment_framework/.venv/bin/python` from this worktree because `.venv/` is gitignored and absent inside the worktree. Do not push, open PRs, publish WeChat drafts, store credentials, or commit unless the user explicitly requests it.

---

## File Structure

- Modify `scripts/continue_single_stock.py`
  - Adds stronger qualitative Step 5 prompt requirements for first-screen summary card, D1-D6 section summaries, narrow-table discipline, appendix-style structured parameters, and article-like deep summary.
- Modify `shared/qualitative/agents/writing_style.md`
  - Makes those same presentation rules part of shared qualitative writing guidance.
- Modify `tests/test_single_stock_prompts.py`
  - Adds prompt coverage for the new Markdown-source optimization rules.
- Modify `scripts/wechat_report.py`
  - Adds qualitative-only `--qualitative-polish`, `--preview-html`, automatic safe digest, polished Markdown generation, and preview generation orchestration.
- Modify `tests/test_wechat_report.py`
  - Adds CLI and helper tests for qualitative polish, digest priority, non-qualitative refusal, validation order, dry-run behavior, and preview behavior.
- Modify `scripts/report_to_html.py`
  - Extracts a reusable `render_report_html()` function and extends `parse_report()` for the upgraded qualitative sections.
- Create `tests/test_report_to_html.py`
  - Adds focused parser/render tests without requiring network or website deployment.
- Modify `shared/qualitative/templates/dashboard.html`
  - Renders first-screen card, core contradiction, future observation variables, and folded structured parameters.

---

### Task 1: Strengthen qualitative Markdown-source prompt rules

**Files:**
- Modify: `tests/test_single_stock_prompts.py`
- Modify: `scripts/continue_single_stock.py`
- Modify: `shared/qualitative/agents/writing_style.md`

- [ ] **Step 1: Write failing prompt test for source Markdown optimization**

Append this test after `test_step5_prompt_requires_wechat_readability_constraints()` in `tests/test_single_stock_prompts.py`:

```python
def test_step5_prompt_requires_wechat_polish_source_structure():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "首屏摘要卡" in prompt
    assert "公司本质" in prompt
    assert "护城河来源" in prompt
    assert "本章小结" in prompt
    assert "3-5 列" in prompt or "3-5列" in prompt
    assert "结构化参数（机器读取 / 附录）" in prompt
    assert "深度总结" in prompt
    assert "公司本质、为什么优势真实、最大风险、重评触发" in prompt
```

- [ ] **Step 2: Run the prompt test and verify it fails**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_single_stock_prompts.py::test_step5_prompt_requires_wechat_polish_source_structure -q
```

Expected: `FAIL` because the current Step 5 prompt does not yet mention `首屏摘要卡`, `本章小结`, appendix-style structured parameters, or the article-like deep summary requirements.

- [ ] **Step 3: Update `build_step5_prompt()` with the new source rules**

In `scripts/continue_single_stock.py`, replace the qualitative instruction block at lines 71-74 with this block:

```python
        + "必须保留并强化成品报告外壳：Business Quality Verdict / 商业质量总体评级、Quality Snapshot / 质量快照、Executive Summary / 执行摘要、核心矛盾与反证条件、未来观察变量、数据来源与免责声明。\n"
        + "首屏必须让读者快速看懂：商业质量评级、公司本质、护城河来源、最大风险、主要约束、周期位置（如适用）、反证条件。\n"
        + "Business Quality Verdict 后必须提供窄版首屏摘要卡，字段包含：公司本质、商业质量、护城河来源、最大风险、周期位置、反证条件。\n"
        + "D1-D6 每个维度在证据充分时必须以“本章小结”收尾，包含本章结论、最重要证据、观察风险 / 重评触发。\n"
        + "未来观察变量必须包含：当前值 / 本地证据、预警阈值、触发后的重评动作。\n"
        + "微信公众号可读性约束：段落不要过长；正文表格优先 3-5 列，宽表只保留关键列；每张表必须服务一个判断并配有结论句；避免审计式数据堆叠。\n"
        + "结构化参数必须保留，但应标为“结构化参数（机器读取 / 附录）”，放在人工阅读结论、观察变量、数据来源和免责声明之后。\n"
        + "深度总结必须像文章结尾一样组织为：公司本质、为什么优势真实、最大风险、重评触发。\n"
```

This changes prompt guidance only; it must not add Muyuan-specific wording or thresholds.

- [ ] **Step 4: Update shared writing style guidance**

In `shared/qualitative/agents/writing_style.md`, extend the `微信公众号 / 网页可读性要求` section by replacing rules 13-17 with this exact text:

```markdown
13. **首屏摘要卡**：Business Quality Verdict 后必须提供窄版首屏摘要卡，回答公司本质、商业质量、护城河来源、最大风险、周期位置（如适用）、反证条件。
14. **章节小结**：D1-D6 每个大维度在证据充分时用“本章小结”收尾，包含本章结论、最重要证据、观察风险 / 重评触发。
15. **短段落**：正文段落尽量控制在 4-6 行 Markdown 源文本以内，超长论证拆成短段或编号列表。
16. **窄表格**：优先使用 3-5 列表格；若数据很多，只保留最能支撑判断的列，且每张表前后必须有一句说明它支持什么判断。
17. **关键数字突出**：关键评级、阈值、异常值和风险触发条件用粗体突出。
18. **避免审计式堆叠**：不要连续罗列大量数据而不解释含义；每组数据必须服务一个判断。
19. **摘要可复用**：Executive Summary 中至少有一句短摘要可作为微信公众号 digest 的基础。
20. **参数附录化**：结构化参数必须保留，但应标为“结构化参数（机器读取 / 附录）”，避免压过人工阅读结论。
21. **文章式结尾**：深度总结按“公司本质 → 为什么优势真实 → 最大风险 → 重评触发”组织，不要只堆维度摘要。
```

- [ ] **Step 5: Run focused prompt tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_single_stock_prompts.py -q
```

Expected: all tests in `tests/test_single_stock_prompts.py` pass.

- [ ] **Step 6: Local checkpoint, no commit**

Run:

```bash
git diff -- tests/test_single_stock_prompts.py scripts/continue_single_stock.py shared/qualitative/agents/writing_style.md
```

Expected: diff only contains prompt/style guidance and the new prompt test. Do not commit.

---

### Task 2: Add qualitative polish helpers and safe digest generation

**Files:**
- Modify: `tests/test_wechat_report.py`
- Modify: `scripts/wechat_report.py`

- [ ] **Step 1: Add a valid qualitative fixture and helper tests**

In `tests/test_wechat_report.py`, add `VALID_QUALITATIVE` after `VALID_VALUATION`:

```python
VALID_QUALITATIVE = """
# 上港集团（600018.SH）— 商业模式与护城河定性分析

> 分析日期：2026-05-09 | 当前股价：¥5.00 | 总市值：¥1,000亿 | A股

## Business Quality Verdict / 商业质量总体评级

综合判断：**B+ / 较强商业质量**。公司依托稀缺港口区位和网络形成稳定现金流，但外贸周期、资本开支和费率机制限制上行弹性。

## Quality Snapshot / 质量快照

| 指标 | 结论 |
|---|---|
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |
| management_rating | 合格 |

## Executive Summary / 执行摘要

上港集团是以港口基础设施和集装箱吞吐网络为核心的区域枢纽型公司，优势来自区位、规模和运营网络，最大约束来自外贸周期与资本开支。

## 核心矛盾与反证条件

核心矛盾是稀缺港口资产带来稳定现金流，但费率弹性和吞吐周期限制利润上行。若吞吐量连续下滑、自由现金流转负或费率机制恶化，应重评商业质量。

## 维度一：商业模式与资本特征

**结论：公司是重资产基础设施平台，收入稳定但资本消耗高。**

### 本章小结

- 本章结论：重资产平台属性明确。
- 最重要证据：收入主要来自港口主业。
- 观察风险 / 重评触发：资本开支持续高于经营现金流。

## 维度二：竞争优势与护城河

**结论：区位和网络形成较强护城河。**

### 本章小结

- 本章结论：优势真实但并非无限定价权。
- 最重要证据：枢纽港网络难以复制。
- 观察风险 / 重评触发：吞吐份额持续下降。

## 维度三：外部环境

**结论：外贸周期决定短期压力。**

### 本章小结

- 本章结论：外部环境中性偏逆风。
- 最重要证据：需求受全球贸易影响。
- 观察风险 / 重评触发：出口景气度恶化。

## 维度四：管理层与治理

**结论：治理底线可接受。**

### 本章小结

- 本章结论：管理层评价合格。
- 最重要证据：分红和资本配置稳定。
- 观察风险 / 重评触发：关联交易异常扩大。

## 维度五：MD&A 解读

**结论：管理层叙事与主业数据大体一致。**

### 本章小结

- 本章结论：叙事可信度中等。
- 最重要证据：经营描述与吞吐量方向一致。
- 观察风险 / 重评触发：叙事与现金流背离。

## 维度六：控股结构分析

**结论：控股结构稳定。**

### 本章小结

- 本章结论：股权结构未构成主要风险。
- 最重要证据：实际控制关系清晰。
- 观察风险 / 重评触发：控制权或质押风险变化。

## 深度总结

公司本质是区域枢纽港口资产。优势真实，因为区位、泊位和网络具有长期稀缺性。最大风险是周期和资本开支共同压低自由现金流。若吞吐份额下降、费率机制恶化或自由现金流持续为负，应重评。

## 未来观察变量

| 变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|
| 吞吐量 | 年报披露稳定 | 连续两年下降 | 下调增长质量 |
| 自由现金流 | 仍需观察 | 连续转负 | 重评资本消耗 |

## 数据来源

年报与本地数据包。

## 免责声明

仅供研究参考，不构成投资建议。

## 结构化参数

| 参数 | 值 |
|---|---|
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |
| management_rating | 合格 |
"""
```

Update the import list at the top of `tests/test_wechat_report.py` to include the helpers that will be implemented:

```python
from wechat_report import (
    auto_digest_from_qualitative,
    build_wxgzh_command,
    create_polished_qualitative_markdown,
    discover_report,
    infer_report_type,
    main,
    polish_qualitative_markdown,
    validate_before_draft,
)
```

Append these tests near the existing helper tests:

```python
def test_qualitative_polish_adds_first_screen_card_and_appendix_label(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    polished = polish_qualitative_markdown(VALID_QUALITATIVE)

    assert "| 项目 | 结论 |" in polished
    assert "| 公司本质 |" in polished
    assert "| 商业质量 |" in polished
    assert "| 护城河来源 |" in polished
    assert "| 最大风险 |" in polished
    assert "| 反证条件 |" in polished
    assert "## 结构化参数（机器读取 / 附录）" in polished
    assert "## 结构化参数\n" not in polished


def test_create_polished_qualitative_markdown_writes_copy_without_changing_original(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")
    output_dir = tmp_path / ".wxgzh"

    polished_path = create_polished_qualitative_markdown(report_path, output_dir)

    assert polished_path == output_dir / "600018_SH_qualitative_report.polished.md"
    assert polished_path.exists()
    assert report_path.read_text(encoding="utf-8") == VALID_QUALITATIVE
    assert "## 结构化参数（机器读取 / 附录）" in polished_path.read_text(encoding="utf-8")


def test_auto_digest_from_qualitative_prefers_executive_summary_and_is_length_limited():
    digest = auto_digest_from_qualitative(VALID_QUALITATIVE)

    assert digest.startswith("上港集团是以港口基础设施")
    assert len(digest) <= 110


def test_auto_digest_from_qualitative_falls_back_to_verdict_then_title():
    without_summary = VALID_QUALITATIVE.replace(
        "## Executive Summary / 执行摘要\n\n上港集团是以港口基础设施和集装箱吞吐网络为核心的区域枢纽型公司，优势来自区位、规模和运营网络，最大约束来自外贸周期与资本开支。\n\n",
        "",
    )
    verdict_digest = auto_digest_from_qualitative(without_summary)
    assert verdict_digest.startswith("综合判断")

    title_only = "# 测试公司（000001.SZ）— 商业模式与护城河定性分析\n"
    assert auto_digest_from_qualitative(title_only) == "测试公司（000001.SZ）商业质量定性分析"
```

- [ ] **Step 2: Run helper tests and verify they fail**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py::test_qualitative_polish_adds_first_screen_card_and_appendix_label tests/test_wechat_report.py::test_create_polished_qualitative_markdown_writes_copy_without_changing_original tests/test_wechat_report.py::test_auto_digest_from_qualitative_prefers_executive_summary_and_is_length_limited tests/test_wechat_report.py::test_auto_digest_from_qualitative_falls_back_to_verdict_then_title -q
```

Expected: import failure because `auto_digest_from_qualitative`, `create_polished_qualitative_markdown`, and `polish_qualitative_markdown` do not exist yet.

- [ ] **Step 3: Implement conservative polish helpers in `scripts/wechat_report.py`**

Add `import re` near the top:

```python
import re
```

Add these helpers after `validate_before_draft()` and before `build_wxgzh_command()`:

```python
def _section_body(md_text: str, title_keywords: tuple[str, ...]) -> str:
    sections = re.split(r"(?=^## )", md_text, flags=re.MULTILINE)
    for section in sections:
        header_match = re.match(r"##\s+(.+?)(?:\n|$)", section)
        if not header_match:
            continue
        title = header_match.group(1)
        if any(keyword in title for keyword in title_keywords):
            return section[header_match.end():].strip()
    return ""


def _first_sentence(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    compact = re.sub(r"^[-*>#\s]+", "", compact)
    match = re.search(r"^(.+?[。！？.!?])", compact)
    return match.group(1).strip() if match else compact


def _trim_digest(text: str, max_chars: int = 110) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip("，,。；;、 ") + "…"


def auto_digest_from_qualitative(md_text: str) -> str:
    summary = _section_body(md_text, ("Executive Summary", "执行摘要"))
    if summary:
        first = _first_sentence(summary)
        if first:
            return _trim_digest(first)

    verdict = _section_body(md_text, ("Business Quality Verdict", "商业质量总体评级"))
    if verdict:
        first = _first_sentence(verdict)
        if first:
            return _trim_digest(first)

    title_match = re.search(r"^#\s+(.+?)(?:—|-|$)", md_text, flags=re.MULTILINE)
    if title_match:
        return _trim_digest(f"{title_match.group(1).strip()}商业质量定性分析")
    return "商业质量定性分析"


def _extract_card_value(md_text: str, keywords: tuple[str, ...], fallback: str = "见正文") -> str:
    for keyword in keywords:
        pattern = rf"(?:{re.escape(keyword)})[：:]\s*\*?\*?(.+?)(?:\*?\*?\s*$|\n)"
        match = re.search(pattern, md_text, flags=re.MULTILINE)
        if match:
            value = match.group(1).strip().strip("* ")
            if value:
                return _trim_digest(value, 80)
    return fallback


def _first_screen_card(md_text: str) -> str:
    company_essence = _extract_card_value(md_text, ("公司本质",), _trim_digest(auto_digest_from_qualitative(md_text), 80))
    quality = _extract_card_value(md_text, ("商业质量", "综合判断", "总体评级"), "见 Business Quality Verdict")
    moat = _extract_card_value(md_text, ("护城河来源", "核心优势", "优势来自"), "见维度二")
    risk = _extract_card_value(md_text, ("最大风险", "核心风险", "主要风险", "主要约束"), "见核心矛盾")
    cycle = _extract_card_value(md_text, ("周期位置", "当前周期"), "不适用 / 见外部环境")
    refutation = _extract_card_value(md_text, ("反证条件", "重评触发", "重评动作"), "见核心矛盾与未来观察变量")
    return "\n".join([
        "| 项目 | 结论 |",
        "|---|---|",
        f"| 公司本质 | {company_essence} |",
        f"| 商业质量 | {quality} |",
        f"| 护城河来源 | {moat} |",
        f"| 最大风险 | {risk} |",
        f"| 周期位置 | {cycle} |",
        f"| 反证条件 | {refutation} |",
    ])


def polish_qualitative_markdown(md_text: str) -> str:
    polished = md_text
    if "| 项目 | 结论 |" not in polished:
        verdict_header = re.search(
            r"(^##\s+.*?(?:Business Quality Verdict|商业质量总体评级).*?\n)",
            polished,
            flags=re.MULTILINE,
        )
        if verdict_header:
            insert_at = verdict_header.end()
            polished = polished[:insert_at] + "\n" + _first_screen_card(polished) + "\n\n" + polished[insert_at:]
    polished = re.sub(
        r"^##\s+结构化参数\s*$",
        "## 结构化参数（机器读取 / 附录）",
        polished,
        flags=re.MULTILINE,
    )
    return polished


def create_polished_qualitative_markdown(report_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    polished_path = output_dir / f"{report_path.stem}.polished.md"
    polished_path.write_text(
        polish_qualitative_markdown(report_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return polished_path
```

- [ ] **Step 4: Run helper tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py::test_qualitative_polish_adds_first_screen_card_and_appendix_label tests/test_wechat_report.py::test_create_polished_qualitative_markdown_writes_copy_without_changing_original tests/test_wechat_report.py::test_auto_digest_from_qualitative_prefers_executive_summary_and_is_length_limited tests/test_wechat_report.py::test_auto_digest_from_qualitative_falls_back_to_verdict_then_title -q
```

Expected: all four tests pass.

- [ ] **Step 5: Run full WeChat tests and verify no regressions**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py -q
```

Expected: all tests in `tests/test_wechat_report.py` pass.

- [ ] **Step 6: Local checkpoint, no commit**

Run:

```bash
git diff -- tests/test_wechat_report.py scripts/wechat_report.py
```

Expected: diff contains only helper tests and conservative polish/digest helpers. Do not commit.

---

### Task 3: Wire `--qualitative-polish` into the WeChat CLI

**Files:**
- Modify: `tests/test_wechat_report.py`
- Modify: `scripts/wechat_report.py`

- [ ] **Step 1: Add CLI tests for polish mode, digest priority, validation order, and type restrictions**

Append these tests to `tests/test_wechat_report.py`:

```python
def test_qualitative_polish_dry_run_uses_polished_markdown_and_auto_digest(tmp_path, monkeypatch, capsys):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--qualitative-polish", "--dry-run"])

    captured = capsys.readouterr()
    polished_path = tmp_path / ".wxgzh" / "600018_SH_qualitative_report.polished.md"
    assert str(polished_path) in captured.out
    assert "--digest" in captured.out
    assert "上港集团是以港口基础设施" in captured.out
    assert polished_path.exists()
    assert report_path.read_text(encoding="utf-8") == VALID_QUALITATIVE


def test_explicit_digest_wins_over_auto_digest_in_qualitative_polish(tmp_path, capsys):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    main([str(report_path), "--qualitative-polish", "--digest", "人工摘要", "--dry-run"])

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

    main([str(report_path), "--qualitative-polish", "--dry-run"])

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
```

- [ ] **Step 2: Run new CLI tests and verify they fail**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py::test_qualitative_polish_dry_run_uses_polished_markdown_and_auto_digest tests/test_wechat_report.py::test_explicit_digest_wins_over_auto_digest_in_qualitative_polish tests/test_wechat_report.py::test_qualitative_polish_runs_validation_before_writing_polished_copy tests/test_wechat_report.py::test_skip_validation_allows_polish_without_validation tests/test_wechat_report.py::test_qualitative_polish_rejects_turtle_and_valuation_reports -q
```

Expected: argument parsing fails because `--qualitative-polish` is not defined yet.

- [ ] **Step 3: Add CLI flags**

In `scripts/wechat_report.py`, add this argument after `--skip-validation`:

```python
    parser.add_argument(
        "--qualitative-polish",
        action="store_true",
        help="Create a presentation-polished qualitative Markdown copy under .wxgzh before drafting",
    )
```

- [ ] **Step 4: Update `main()` to validate first, then polish, then build command**

Replace `main()` lines 113-135 with this implementation:

```python
def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    report_path = discover_report(args.path, args.type, args.file)
    report_type = args.type or infer_report_type(report_path)
    if args.qualitative_polish and report_type != "qualitative":
        raise SystemExit("--qualitative-polish only supports qualitative reports")

    if not args.skip_validation:
        validate_before_draft(report_path, report_type)

    output_dir = args.output_dir or report_path.parent / ".wxgzh"
    draft_report_path = report_path
    digest = args.digest
    if args.qualitative_polish:
        draft_report_path = create_polished_qualitative_markdown(report_path, output_dir)
        if digest is None:
            digest = auto_digest_from_qualitative(report_path.read_text(encoding="utf-8"))

    command = build_wxgzh_command(
        draft_report_path,
        output_dir=output_dir,
        account=args.account,
        author=args.author,
        digest=digest,
        theme=args.theme,
        cover=args.cover,
        no_cover=args.no_cover,
    )
    if args.dry_run:
        print(shlex.join(command))
        return
    if not args.yes:
        raise SystemExit("--yes is required for real draft creation")
    subprocess.run(command, check=True)
```

- [ ] **Step 5: Update existing real-run expectation**

In `test_real_run_executes_npx_when_yes_is_explicit`, no behavior changes are expected for valuation. If the test fails because of local variable renaming, keep the expected command exactly as:

```python
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
```

- [ ] **Step 6: Run WeChat tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py -q
```

Expected: all WeChat tests pass; existing turtle and valuation behavior remains unchanged.

- [ ] **Step 7: Local checkpoint, no commit**

Run:

```bash
git diff -- tests/test_wechat_report.py scripts/wechat_report.py
```

Expected: diff shows qualitative-only CLI integration and tests. Do not commit.

---

### Task 4: Refactor HTML renderer into a reusable function and parse upgraded qualitative sections

**Files:**
- Create: `tests/test_report_to_html.py`
- Modify: `scripts/report_to_html.py`
- Modify: `shared/qualitative/templates/dashboard.html`

- [ ] **Step 1: Create parser/render tests**

Create `tests/test_report_to_html.py` with this content:

```python
from pathlib import Path

from report_to_html import parse_report, render_report_html


QUALITATIVE_WITH_POLISH_SECTIONS = """
# 上港集团（600018.SH）— 商业模式与护城河定性分析

> 分析日期：2026-05-09 | 当前股价：¥5.00 | 总市值：¥1,000亿 | A股

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 区域枢纽港口资产 |
| 商业质量 | B+ / 较强 |
| 护城河来源 | 区位、规模、网络 |
| 最大风险 | 外贸周期和资本开支 |
| 周期位置 | 中性偏逆风 |
| 反证条件 | 吞吐份额下降或自由现金流转负 |

综合判断：**B+ / 较强商业质量**。

## Quality Snapshot / 质量快照

| 指标 | 结论 |
|---|---|
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |

## Executive Summary / 执行摘要

上港集团是区域枢纽港口资产。

## 核心矛盾与反证条件

核心矛盾是稀缺资产和周期约束并存。若自由现金流持续为负，应重评。

## 维度一：商业模式与资本特征

**结论：重资产但现金流稳定。**

### 本章小结

- 本章结论：平台属性明确。
- 最重要证据：港口主业稳定。
- 观察风险 / 重评触发：资本开支过高。

## 深度总结

公司本质是区域枢纽港口资产。优势真实但受周期约束。

## 未来观察变量

| 变量 | 当前值 / 本地证据 | 预警阈值 | 触发后的重评动作 |
|---|---|---|---|
| 吞吐量 | 年报披露稳定 | 连续两年下降 | 下调增长质量 |

## 数据来源

年报与本地数据包。

## 免责声明

仅供研究参考。

## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| moat_rating | 较强 |
"""


def test_parse_report_extracts_upgraded_qualitative_sections():
    report = parse_report(QUALITATIVE_WITH_POLISH_SECTIONS)

    assert "项目" in report["first_screen_card"]
    assert "核心矛盾" in report["core_contradiction"]
    assert "触发后的重评动作" in report["future_observations"]
    assert "moat_rating" in report["parameters_table"]
    assert report["conclusion"]
    assert len(report["dimensions"]) == 1


def test_render_report_html_writes_local_preview_with_upgraded_sections(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.polished.md"
    output_path = tmp_path / "600018_SH_qualitative_report.preview.html"
    report_path.write_text(QUALITATIVE_WITH_POLISH_SECTIONS, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "首屏摘要" in html
    assert "核心矛盾与反证条件" in html
    assert "未来观察变量" in html
    assert "结构化参数" in html
    assert "<details" in html
```

- [ ] **Step 2: Run new HTML tests and verify they fail**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_report_to_html.py -q
```

Expected: import failure because `render_report_html` does not exist and `parse_report()` does not yet expose `first_screen_card`, `core_contradiction`, or `future_observations`.

- [ ] **Step 3: Extend `parse_report()` result keys**

In `scripts/report_to_html.py`, update the `result` dictionary in `parse_report()` to include:

```python
        "first_screen_card": "",
        "core_contradiction": "",
        "future_observations": "",
```

Then update the section loop in `parse_report()` so these sections are recognized before the generic `维度` branch:

```python
        if "执行摘要" in title or "Executive Summary" in title:
            result["executive_summary"] = md_to_html(body)
        elif "Business Quality Verdict" in title or "商业质量总体评级" in title:
            table_match = re.search(r"((?:\|.*\|\n)+)", body)
            if table_match and "项目" in table_match.group(1) and "结论" in table_match.group(1):
                result["first_screen_card"] = md_to_html(table_match.group(1))
        elif "核心矛盾" in title or "反证条件" in title:
            result["core_contradiction"] = md_to_html(body)
        elif "未来观察" in title or "观察变量" in title:
            result["future_observations"] = md_to_html(body)
        elif "总结与投资启示" in title or "深度总结" in title:
            result["conclusion"] = md_to_html(body)
        elif "结构化参数" in title:
            result["parameters_table"] = md_to_html(body)
```

Keep the existing `交叉验证` and `维度` branches after these section branches.

- [ ] **Step 4: Extract `render_report_html()` from `main()`**

In `scripts/report_to_html.py`, add this function before `main()`:

```python
def render_report_html(
    input_path: Path,
    output_path: Path,
    *,
    template_path: Path | None = None,
    appendix_path: Path | None = None,
    data_pack_path: Path | None = None,
    standalone: bool = False,
) -> None:
    project_root = Path(__file__).resolve().parent.parent
    template_path = template_path or project_root / "shared" / "qualitative" / "templates" / "dashboard.html"
    appendix_path = appendix_path or project_root / "shared" / "qualitative" / "references" / "framework_guide.md"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    md_text = input_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    appendix_html = ""
    if appendix_path.exists():
        appendix_md = appendix_path.read_text(encoding="utf-8")
        appendix_html = md_to_html(appendix_md)

    report = parse_report(md_text)
    kpi_cards = extract_kpi_cards(md_text)
    verdict = build_verdict(md_text)

    dp_info = {"current_price": "", "market_cap": "", "exchange": "", "industry": ""}
    resolved_data_pack = data_pack_path or input_path.parent / "data_pack_market.md"
    if resolved_data_pack.exists():
        dp_text = resolved_data_pack.read_text(encoding="utf-8")
        dp_info = extract_data_pack_info(dp_text)

    standalone_css = ""
    if standalone:
        site_root = Path.home() / "Projects" / "Teracnejiang.com"
        css_parts = []
        for css_file in ["assets/css/style.css", "assets/css/report.css"]:
            css_path = site_root / css_file
            if css_path.exists():
                css_parts.append(css_path.read_text(encoding="utf-8"))
        standalone_css = "\n".join(css_parts) if css_parts else _FALLBACK_CSS

    slug = ""
    if report["stock_code"]:
        code = report["stock_code"].replace(".SH", "").replace(".SZ", "").replace(".HK", "").replace(".US", "")
        name = report["company_name"] or ""
        slug = f"{name}-{code}-qualitative".lower().replace(" ", "-")

    env = Environment(loader=BaseLoader())
    template = env.from_string(template_text)
    html = template.render(
        company_name=report["company_name"],
        stock_code=report["stock_code"],
        generated_date=report["generated_date"],
        current_price=dp_info["current_price"],
        market_cap=dp_info["market_cap"],
        exchange=dp_info["exchange"],
        industry=dp_info["industry"],
        slug=slug,
        standalone_css=standalone_css,
        kpi_cards=kpi_cards,
        first_screen_card=report["first_screen_card"],
        core_contradiction=report["core_contradiction"],
        future_observations=report["future_observations"],
        executive_summary=report["executive_summary"],
        dimensions=report["dimensions"],
        conclusion=report["conclusion"],
        parameters_table=report["parameters_table"],
        framework_guide=appendix_html,
        **verdict,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
```

Then replace the body of `main()` after argument parsing with:

```python
    input_path = Path(args.input)
    output_path = Path(args.output)
    template_path = Path(args.template) if args.template else None
    appendix_path = Path(args.appendix) if args.appendix else None
    data_pack_path = Path(args.data_pack) if args.data_pack else None

    try:
        render_report_html(
            input_path,
            output_path,
            template_path=template_path,
            appendix_path=appendix_path,
            data_pack_path=data_pack_path,
            standalone=args.standalone,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    report = parse_report(input_path.read_text(encoding="utf-8"))
    kpi_cards = extract_kpi_cards(input_path.read_text(encoding="utf-8"))
    appendix_exists = (appendix_path or Path(__file__).resolve().parent.parent / "shared" / "qualitative" / "references" / "framework_guide.md").exists()
    print(f"HTML report generated: {output_path}")
    print(f"  Sections: {len(report['dimensions'])} dimensions")
    print(f"  KPI cards: {len(kpi_cards)}")
    print(f"  Has executive summary: {bool(report['executive_summary'])}")
    print(f"  Has conclusion: {bool(report['conclusion'])}")
    print(f"  Has appendix: {appendix_exists}")
```

- [ ] **Step 5: Update the template to render upgraded sections**

In `shared/qualitative/templates/dashboard.html`, insert this block after the verdict block and before `<!-- KPI Snapshot -->`:

```html
<!-- First-screen Card -->
{% if first_screen_card %}
<h2>首屏摘要</h2>
<div class="callout first-screen-card">
  {{ first_screen_card }}
</div>
{% endif %}
```

Insert this block after the Executive Summary block and before `<!-- Dimension Sections -->`:

```html
<!-- Core Contradiction -->
{% if core_contradiction %}
<h2>核心矛盾与反证条件</h2>
<div class="callout core-contradiction">
  {{ core_contradiction }}
</div>
{% endif %}

<!-- Future Observations -->
{% if future_observations %}
<h2>未来观察变量</h2>
<div class="callout future-observations">
  {{ future_observations }}
</div>
{% endif %}
```

Change the structured parameters summary from:

```html
  <summary>Structured Parameters · 结构化参数表</summary>
```

to:

```html
  <summary>Structured Parameters · 结构化参数（机器读取 / 附录）</summary>
```

- [ ] **Step 6: Add local preview CSS support**

In `_FALLBACK_CSS` in `scripts/report_to_html.py`, after the existing `.report-body .callout` rule, append this CSS fragment inside the string:

```css
.report-body .first-screen-card table,.report-body .future-observations table{margin:0}.report-body .first-screen-card td:not(:first-child),.report-body .future-observations td:not(:first-child){text-align:left;font-family:inherit}.report-body .core-contradiction{border-left:4px solid var(--amber)}
```

- [ ] **Step 7: Run HTML tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_report_to_html.py -q
```

Expected: both HTML tests pass.

- [ ] **Step 8: Run current report_to_html CLI smoke test**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python scripts/report_to_html.py --input /Users/rushmind/Turtle_investment_framework/output/002714_e2e_fresh/002714_SZ_qualitative_report.md --output /tmp/002714_SZ_qualitative_report.preview.html --standalone
```

Expected: command exits 0 and prints `HTML report generated: /tmp/002714_SZ_qualitative_report.preview.html`.

- [ ] **Step 9: Local checkpoint, no commit**

Run:

```bash
git diff -- tests/test_report_to_html.py scripts/report_to_html.py shared/qualitative/templates/dashboard.html
```

Expected: diff contains parser/render/template changes only. Do not commit.

---

### Task 5: Add `--preview-html` support to qualitative polish mode

**Files:**
- Modify: `tests/test_wechat_report.py`
- Modify: `scripts/wechat_report.py`

- [ ] **Step 1: Add preview CLI tests**

Append these tests to `tests/test_wechat_report.py`:

```python
def test_preview_html_with_qualitative_polish_writes_preview_without_network(tmp_path, monkeypatch):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    def fail_run(*args, **kwargs):
        raise AssertionError("preview dry-run must not call subprocess.run")

    monkeypatch.setattr(subprocess, "run", fail_run)

    main([str(report_path), "--qualitative-polish", "--preview-html", "--dry-run"])

    preview_path = tmp_path / ".wxgzh" / "600018_SH_qualitative_report.preview.html"
    assert preview_path.exists()
    html = preview_path.read_text(encoding="utf-8")
    assert "核心矛盾与反证条件" in html
    assert "未来观察变量" in html
    assert "结构化参数" in html


def test_preview_html_requires_qualitative_polish(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.md"
    report_path.write_text(VALID_QUALITATIVE, encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main([str(report_path), "--preview-html", "--dry-run"])

    assert "--preview-html requires --qualitative-polish" in str(exc.value)
```

- [ ] **Step 2: Run preview tests and verify they fail**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py::test_preview_html_with_qualitative_polish_writes_preview_without_network tests/test_wechat_report.py::test_preview_html_requires_qualitative_polish -q
```

Expected: argument parsing fails because `--preview-html` is not defined yet.

- [ ] **Step 3: Import the reusable renderer**

In `scripts/wechat_report.py`, add this import after `from validate_reports import validate_file`:

```python
from report_to_html import render_report_html
```

- [ ] **Step 4: Add `--preview-html` argument**

In `_parse_args()`, add after `--qualitative-polish`:

```python
    parser.add_argument(
        "--preview-html",
        action="store_true",
        help="Generate a local standalone HTML preview for qualitative polish mode",
    )
```

- [ ] **Step 5: Add preview path helper**

Add this helper after `create_polished_qualitative_markdown()`:

```python
def preview_html_path_for(report_path: Path, output_dir: Path) -> Path:
    stem = report_path.stem
    if stem.endswith(".polished"):
        stem = stem.removesuffix(".polished")
    return output_dir / f"{stem}.preview.html"
```

- [ ] **Step 6: Wire preview generation into `main()`**

In `main()`, after the `if args.qualitative_polish:` block that creates `draft_report_path`, add:

```python
    if args.preview_html and not args.qualitative_polish:
        raise SystemExit("--preview-html requires --qualitative-polish")
    if args.preview_html:
        preview_path = preview_html_path_for(draft_report_path, output_dir)
        render_report_html(draft_report_path, preview_path, standalone=True)
```

Place the `--preview-html requires --qualitative-polish` check before any preview generation. Validation should still run before polish/preview unless `--skip-validation` is provided.

- [ ] **Step 7: Run WeChat preview tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py::test_preview_html_with_qualitative_polish_writes_preview_without_network tests/test_wechat_report.py::test_preview_html_requires_qualitative_polish -q
```

Expected: both tests pass and no subprocess call occurs in dry-run mode.

- [ ] **Step 8: Run full WeChat tests and verify they pass**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py -q
```

Expected: all WeChat tests pass.

- [ ] **Step 9: Local checkpoint, no commit**

Run:

```bash
git diff -- tests/test_wechat_report.py scripts/wechat_report.py
```

Expected: diff shows preview tests and preview orchestration only. Do not commit.

---

### Task 6: Focused and regression verification

**Files:**
- Verify only; no edits expected.

- [ ] **Step 1: Run focused prompt tests**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_single_stock_prompts.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run focused WeChat tests**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_wechat_report.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run focused HTML tests**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_report_to_html.py -q
```

Expected: all tests pass.

- [ ] **Step 4: Run validator regression tests**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_validate_reports.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Run build data pack regression tests**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_build_data_pack_report.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Run combined focused suite**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests/test_single_stock_prompts.py tests/test_wechat_report.py tests/test_report_to_html.py tests/test_validate_reports.py tests/test_build_data_pack_report.py -q
```

Expected: combined suite passes.

- [ ] **Step 7: Run non-integration suite if focused suite passes**

Run:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python -m pytest tests -q -m "not integration"
```

Expected: non-integration tests pass.

- [ ] **Step 8: Manual smoke for real qualitative output polish and preview**

Run from the worktree:

```bash
PYTHONPATH=scripts /Users/rushmind/Turtle_investment_framework/.venv/bin/python scripts/wechat_report.py /Users/rushmind/Turtle_investment_framework/output/002714_e2e_fresh --type qualitative --qualitative-polish --preview-html --dry-run
```

Expected:

- command exits 0;
- prints an `npx -y @lyhue1991/wxgzh` dry-run command;
- command uses `/Users/rushmind/Turtle_investment_framework/output/002714_e2e_fresh/.wxgzh/002714_SZ_qualitative_report.polished.md`;
- command includes `--digest` with a short digest;
- writes `/Users/rushmind/Turtle_investment_framework/output/002714_e2e_fresh/.wxgzh/002714_SZ_qualitative_report.polished.md`;
- writes `/Users/rushmind/Turtle_investment_framework/output/002714_e2e_fresh/.wxgzh/002714_SZ_qualitative_report.preview.html`;
- does not call the WeChat API because `--dry-run` is present.

- [ ] **Step 9: Inspect final diff**

Run:

```bash
git status --short
git diff --stat
git diff -- scripts/continue_single_stock.py scripts/wechat_report.py scripts/report_to_html.py shared/qualitative/agents/writing_style.md shared/qualitative/templates/dashboard.html tests/test_single_stock_prompts.py tests/test_wechat_report.py tests/test_report_to_html.py
```

Expected: changed files match this plan, no generated `.wxgzh` artifacts are staged or committed, and no credentials appear in the diff.

---

## Self-Review Checklist

- Spec coverage:
  - First-screen summary card: Task 1 prompt rules, Task 2 polish helper, Task 4 HTML rendering.
  - D1-D6 section summaries: Task 1 prompt/style rules.
  - Narrow-table discipline: Task 1 prompt/style rules.
  - Structured parameters as appendix: Task 1 prompt/style rules, Task 2 polish helper, Task 4 folded template.
  - Article-like deep summary: Task 1 prompt/style rules.
  - Qualitative-only polish mode: Task 3.
  - Safe auto digest: Task 2 and Task 3.
  - Preview HTML: Task 4 and Task 5.
  - Turtle/valuation unchanged: Task 3 tests and Task 6 regression suite.
  - No Muyuan-specific implementation: all examples use generic section structure; helper logic uses headings and section terms, not company-specific thresholds.
- Placeholder scan: no unresolved placeholder markers or incomplete task text.
- Type/signature consistency:
  - `polish_qualitative_markdown(md_text: str) -> str`
  - `create_polished_qualitative_markdown(report_path: Path, output_dir: Path) -> Path`
  - `auto_digest_from_qualitative(md_text: str) -> str`
  - `render_report_html(input_path: Path, output_path: Path, *, template_path: Path | None = None, appendix_path: Path | None = None, data_pack_path: Path | None = None, standalone: bool = False) -> None`
  - `preview_html_path_for(report_path: Path, output_dir: Path) -> Path`
