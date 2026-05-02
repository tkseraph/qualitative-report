# Three Report Schema Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a checkable product schema and validator for the three A-share finished reports: qualitative, turtle, and valuation.

**Architecture:** Add a small Python schema module that defines required report sections, top-of-page components, and keyword-level evidence for each report type learned from the SIPG reference pages. Add a validator CLI that checks Markdown reports and optional output directories, returning actionable missing-item messages without invoking LLMs or changing report generation. Keep HTML conversion unchanged in this first step; this task creates the contract that later prompt/HTML/runner work will target.

**Tech Stack:** Python 3.10+, stdlib dataclasses/argparse/re/pathlib, pytest.

---

## File Structure

- Create `scripts/report_schema.py`
  - Owns the human-readable, machine-checkable schema for the shared page structure and each report type.
  - Exposes `REPORT_SCHEMAS`, `ReportSchema`, and `SchemaRequirement`.

- Create `scripts/validate_reports.py`
  - CLI and library validator for one Markdown file or an output directory.
  - Exposes `validate_markdown(text, report_type)`, `validate_file(path, report_type)`, and `validate_output_dir(output_dir)`.
  - Does not generate reports or mutate files.

- Create `tests/test_report_schema.py`
  - Tests schema completeness and A-share-only scope.

- Create `tests/test_validate_reports.py`
  - Tests validator behavior on minimal valid samples and missing-section failures.

- Modify `README.md`
  - Add a short usage section for validating the three finished reports.

- Defer to later plans:
  - Updating prompts/coordinators to conform to the schema.
  - Refactoring `run_single_stock.py` into a full orchestrator.
  - HTML visual parity improvements.

---

### Task 1: Add Report Schema Definitions

**Files:**
- Create: `scripts/report_schema.py`
- Test: `tests/test_report_schema.py`

- [ ] **Step 1: Write failing schema tests**

Create `tests/test_report_schema.py` with this content:

```python
from report_schema import REPORT_SCHEMAS


def test_defines_exactly_three_report_types():
    assert set(REPORT_SCHEMAS) == {"qualitative", "turtle", "valuation"}


def test_all_report_schemas_require_shared_finished_page_components():
    for schema in REPORT_SCHEMAS.values():
        requirement_names = {requirement.name for requirement in schema.requirements}
        assert "verdict banner" in requirement_names
        assert "snapshot cards" in requirement_names
        assert "executive summary" in requirement_names
        assert "data sources" in requirement_names
        assert "disclaimer" in requirement_names


def test_qualitative_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["qualitative"].requirements}
    expected = {
        "business quality verdict",
        "quality snapshot",
        "six dimensions",
        "deep summary",
        "future observation variables",
        "structured parameters",
    }
    assert expected.issubset(requirement_names)


def test_turtle_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["turtle"].requirements}
    expected = {
        "strategy verdict",
        "turtle snapshot",
        "owner earnings",
        "penetrating return",
        "safety margin",
        "value-trap filters",
        "thesis card",
        "fundamental stop-loss rules",
        "event monitoring checklist",
    }
    assert expected.issubset(requirement_names)


def test_valuation_schema_matches_target_case_components():
    requirement_names = {requirement.name for requirement in REPORT_SCHEMAS["valuation"].requirements}
    expected = {
        "valuation verdict",
        "valuation snapshot",
        "company classification",
        "method weights",
        "wacc",
        "qualitative adjustments",
        "dcf",
        "pe band",
        "ddm",
        "cross-validation",
        "reverse valuation",
        "valuation range",
    }
    assert expected.issubset(requirement_names)


def test_scope_is_a_share_only():
    for schema in REPORT_SCHEMAS.values():
        assert schema.market_scope == "A-share"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_report_schema.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'report_schema'`.

- [ ] **Step 3: Implement schema module**

Create `scripts/report_schema.py` with this content:

```python
"""Finished-report schemas for the A-share three-report product."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SchemaRequirement:
    name: str
    any_keywords: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ReportSchema:
    report_type: str
    display_name: str
    market_scope: str
    requirements: tuple[SchemaRequirement, ...]


SHARED_REQUIREMENTS: tuple[SchemaRequirement, ...] = (
    SchemaRequirement(
        "verdict banner",
        ("Verdict", "总体评级", "核心判定", "估值判断", "仓位建议"),
        "First-screen conclusion block that states the report's main judgment.",
    ),
    SchemaRequirement(
        "snapshot cards",
        ("Snapshot", "快照", "KPI", "核心指标"),
        "First-screen metric cards summarizing the most important report metrics.",
    ),
    SchemaRequirement(
        "executive summary",
        ("Executive Summary", "执行摘要"),
        "Concise conclusion-first summary before detailed analysis.",
    ),
    SchemaRequirement(
        "data sources",
        ("数据来源", "Data Source", "Data Sources"),
        "Explicit source disclosure for market, financial, report, and model data.",
    ),
    SchemaRequirement(
        "disclaimer",
        ("免责声明", "不构成投资建议", "仅供研究参考"),
        "Research-only disclaimer and AI-assisted generation notice.",
    ),
)


QUALITATIVE_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "business quality verdict",
        ("Business Quality Verdict", "商业质量", "护城河"),
        "Top judgment for business quality and moat strength.",
    ),
    SchemaRequirement(
        "quality snapshot",
        ("Quality Snapshot", "质量快照", "5年平均ROE", "护城河评级"),
        "KPI cards for ROE, moat, sustainability, management, cycle, capital intensity, and barriers.",
    ),
    SchemaRequirement(
        "six dimensions",
        ("维度一", "维度二", "维度三", "维度四", "维度五", "维度六"),
        "D1-D6 qualitative analysis structure.",
    ),
    SchemaRequirement(
        "deep summary",
        ("深度总结", "核心投资逻辑", "优势与风险"),
        "Integrated conclusion that weighs core logic, advantages, and risks.",
    ),
    SchemaRequirement(
        "future observation variables",
        ("未来观察", "观察变量", "监控KPI"),
        "Forward-looking monitoring variables for future review.",
    ),
    SchemaRequirement(
        "structured parameters",
        ("结构化参数", "structured parameters", "moat_rating", "roe_5y_avg"),
        "Machine-readable parameter table for downstream turtle and valuation reports.",
    ),
)


TURTLE_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "strategy verdict",
        ("Strategy Verdict", "OBSERVE", "WAIT", "BUY", "AVOID", "仓位建议"),
        "Top investment action and strategy judgment.",
    ),
    SchemaRequirement(
        "turtle snapshot",
        ("Turtle Snapshot", "穿透回报率", "门槛收益率", "安全边际"),
        "KPI cards for penetrating return, hurdle rate, margin of safety, moat, and risk state.",
    ),
    SchemaRequirement(
        "owner earnings",
        ("Owner Earnings", "所有者收益", "OE"),
        "Owner Earnings bridge from reported profit and maintenance capex.",
    ),
    SchemaRequirement(
        "penetrating return",
        ("穿透回报率", "精算", "粗算"),
        "Penetrating return analysis and credibility distinction between rough and refined calculations.",
    ),
    SchemaRequirement(
        "safety margin",
        ("安全边际", "门槛", "margin of safety"),
        "Comparison between refined return and hurdle rate.",
    ),
    SchemaRequirement(
        "value-trap filters",
        ("价值陷阱", "过滤器", "风险等级"),
        "Explicit value-trap checklist and risk rating.",
    ),
    SchemaRequirement(
        "thesis card",
        ("投资论点卡", "Thesis Card", "核心论点"),
        "Investment thesis card with balanced bull/bear framing.",
    ),
    SchemaRequirement(
        "fundamental stop-loss rules",
        ("基本面止损", "止损条件", "critical", "warning"),
        "Structured fundamental stop-loss triggers.",
    ),
    SchemaRequirement(
        "event monitoring checklist",
        ("事件监控", "监控清单", "关键词"),
        "Event and keyword monitoring checklist.",
    ),
)


VALUATION_REQUIREMENTS: tuple[SchemaRequirement, ...] = SHARED_REQUIREMENTS + (
    SchemaRequirement(
        "valuation verdict",
        ("Valuation Verdict", "估值判断", "内在价值"),
        "Top valuation state and price-versus-value judgment.",
    ),
    SchemaRequirement(
        "valuation snapshot",
        ("Valuation Snapshot", "估值快照", "安全边际", "WACC"),
        "KPI cards for intrinsic value, safety margin, company type, methods, and WACC.",
    ),
    SchemaRequirement(
        "company classification",
        ("公司分类", "蓝筹", "成长", "混合型"),
        "Company type classification that drives valuation method selection.",
    ),
    SchemaRequirement(
        "method weights",
        ("方法权重", "权重", "估值方法选择"),
        "Selected valuation methods and their weights.",
    ),
    SchemaRequirement(
        "wacc",
        ("WACC", "资本成本", "权益成本"),
        "Capital cost calculation and risk adjustment.",
    ),
    SchemaRequirement(
        "qualitative adjustments",
        ("定性调整", "调整依据", "原模型值", "调整后"),
        "Mapping from qualitative conclusions to model assumptions.",
    ),
    SchemaRequirement(
        "dcf",
        ("DCF", "自由现金流", "永续增长率"),
        "DCF assumptions, result, and sensitivity analysis.",
    ),
    SchemaRequirement(
        "pe band",
        ("PE Band", "PE", "历史分位"),
        "Market multiple valuation using historical PE bands.",
    ),
    SchemaRequirement(
        "ddm",
        ("DDM", "股息", "DPS", "分红"),
        "Dividend discount model with payout and growth explanation.",
    ),
    SchemaRequirement(
        "cross-validation",
        ("交叉验证", "CV", "一致性"),
        "Weighted cross-validation across valuation methods.",
    ),
    SchemaRequirement(
        "reverse valuation",
        ("反向估值", "隐含", "市场预期"),
        "Reverse valuation from market price to implied expectations.",
    ),
    SchemaRequirement(
        "valuation range",
        ("估值区间", "保守", "中性", "乐观"),
        "Final valuation range and current price position.",
    ),
)


REPORT_SCHEMAS: dict[str, ReportSchema] = {
    "qualitative": ReportSchema(
        report_type="qualitative",
        display_name="商业质量评估报告",
        market_scope="A-share",
        requirements=QUALITATIVE_REQUIREMENTS,
    ),
    "turtle": ReportSchema(
        report_type="turtle",
        display_name="龟龟投资策略分析报告",
        market_scope="A-share",
        requirements=TURTLE_REQUIREMENTS,
    ),
    "valuation": ReportSchema(
        report_type="valuation",
        display_name="估值分析报告",
        market_scope="A-share",
        requirements=VALUATION_REQUIREMENTS,
    ),
}
```

- [ ] **Step 4: Run schema tests**

Run:

```bash
python -m pytest tests/test_report_schema.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit schema task**

Run:

```bash
git add scripts/report_schema.py tests/test_report_schema.py
git commit -m "feat: define three report product schemas"
```

Expected: commit succeeds.

---

### Task 2: Add Markdown Validator Library

**Files:**
- Create: `scripts/validate_reports.py`
- Modify: `tests/test_validate_reports.py`

- [ ] **Step 1: Write failing validator tests**

Create `tests/test_validate_reports.py` with this content:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_validate_reports.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'validate_reports'`.

- [ ] **Step 3: Implement validator library**

Create `scripts/validate_reports.py` with this content:

```python
#!/usr/bin/env python3
"""Validate finished report Markdown files against product schemas."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from report_schema import REPORT_SCHEMAS, ReportSchema, SchemaRequirement


@dataclass(frozen=True)
class ValidationResult:
    report_type: str
    path: str
    ok: bool
    missing: list[str]
    messages: list[str]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _has_any_keyword(normalized_text: str, requirement: SchemaRequirement) -> bool:
    return any(keyword.lower() in normalized_text for keyword in requirement.any_keywords)


def _missing_requirements(md_text: str, schema: ReportSchema) -> list[SchemaRequirement]:
    normalized = _normalize(md_text)
    return [
        requirement
        for requirement in schema.requirements
        if not _has_any_keyword(normalized, requirement)
    ]


def validate_markdown(md_text: str, report_type: str, path: str = "<memory>") -> ValidationResult:
    schema = REPORT_SCHEMAS.get(report_type)
    if schema is None:
        known = ", ".join(sorted(REPORT_SCHEMAS))
        return ValidationResult(
            report_type=report_type,
            path=path,
            ok=False,
            missing=[report_type],
            messages=[f"Unknown report type: {report_type}. Expected one of: {known}"],
        )

    missing_requirements = _missing_requirements(md_text, schema)
    messages = [
        f"Missing {requirement.name}: {requirement.description} "
        f"(expected one of: {', '.join(requirement.any_keywords)})"
        for requirement in missing_requirements
    ]
    return ValidationResult(
        report_type=report_type,
        path=path,
        ok=not missing_requirements,
        missing=[requirement.name for requirement in missing_requirements],
        messages=messages,
    )


def validate_file(path: Path, report_type: str) -> ValidationResult:
    if not path.exists():
        return ValidationResult(
            report_type=report_type,
            path=str(path),
            ok=False,
            missing=["file"],
            messages=[f"Missing file: {path}"],
        )
    return validate_markdown(path.read_text(encoding="utf-8"), report_type, str(path))


def _find_one(output_dir: Path, pattern: str) -> Path | None:
    matches = sorted(output_dir.glob(pattern))
    return matches[0] if matches else None


def validate_output_dir(output_dir: Path) -> list[ValidationResult]:
    report_files = {
        "qualitative": _find_one(output_dir, "*_qualitative_report.md"),
        "turtle": _find_one(output_dir, "*_turtle_report.md"),
        "valuation": _find_one(output_dir, "*_valuation_report.md"),
    }
    results: list[ValidationResult] = []
    for report_type, path in report_files.items():
        if path is None:
            expected = output_dir / f"*_{report_type}_report.md"
            results.append(
                ValidationResult(
                    report_type=report_type,
                    path=str(expected),
                    ok=False,
                    missing=["file"],
                    messages=[f"Missing {report_type} report matching {expected}"],
                )
            )
        else:
            results.append(validate_file(path, report_type))
    return results


def _print_result(result: ValidationResult) -> None:
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] {result.report_type}: {result.path}")
    for message in result.messages:
        print(f"  - {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate finished A-share report outputs")
    parser.add_argument("path", help="Markdown report file or output directory")
    parser.add_argument(
        "--type",
        choices=sorted(REPORT_SCHEMAS),
        help="Report type when validating a single Markdown file",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_dir():
        results = validate_output_dir(path)
    else:
        if args.type is None:
            raise SystemExit("--type is required when validating a single Markdown file")
        results = [validate_file(path, args.type)]

    for result in results:
        _print_result(result)

    if not all(result.ok for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run validator tests**

Run:

```bash
python -m pytest tests/test_validate_reports.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit validator library task**

Run:

```bash
git add scripts/validate_reports.py tests/test_validate_reports.py
git commit -m "feat: validate finished report schemas"
```

Expected: commit succeeds.

---

### Task 3: Add Output Directory Validation Tests and CLI Coverage

**Files:**
- Modify: `tests/test_validate_reports.py`

- [ ] **Step 1: Add output directory tests**

Append this content to `tests/test_validate_reports.py`:

```python
from pathlib import Path

from validate_reports import validate_output_dir


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
```

- [ ] **Step 2: Run tests**

Run:

```bash
python -m pytest tests/test_validate_reports.py -v
```

Expected: PASS.

- [ ] **Step 3: Run CLI manually on a sample output directory**

Run:

```bash
python scripts/validate_reports.py output/000538_acceptance
```

Expected: command may PASS or FAIL depending on current sample report structure. If it fails, do not change samples in this task; record the missing schema items in the final summary because this validator is intended to expose template gaps.

- [ ] **Step 4: Commit output-directory validation task**

Run:

```bash
git add tests/test_validate_reports.py
git commit -m "test: cover three report output validation"
```

Expected: commit succeeds.

---

### Task 4: Document Validator Usage

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add README test that checks command mention**

Append this test to `tests/test_validate_reports.py`:

```python

def test_readme_documents_report_validator():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "validate_reports.py" in readme
    assert "三报告成品验收" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_validate_reports.py::test_readme_documents_report_validator -v
```

Expected: FAIL because README does not document the validator yet.

- [ ] **Step 3: Add README section**

In `README.md`, add this section after the single-stock runner / continuation usage section, before the data collection section:

```markdown
### 三报告成品验收

`scripts/validate_reports.py` 用于检查一个 A 股标的输出目录是否已经达到三份正式报告的基础成品结构。它不会生成报告，只检查 qualitative、turtle、valuation 三份 Markdown 是否包含目标网页案例抽象出的关键模块。

```bash
# 检查一个完整 output 目录
python scripts/validate_reports.py output/000538_acceptance

# 检查单个报告文件
python scripts/validate_reports.py \
  output/000538_acceptance/000538_SZ_valuation_report.md \
  --type valuation
```

验收器覆盖的核心结构：
- qualitative：Business Quality Verdict、Quality Snapshot、D1-D6、深度总结、观察变量、结构化参数、数据来源、免责声明。
- turtle：Strategy Verdict、Turtle Snapshot、Owner Earnings、穿透回报率、安全边际、价值陷阱、投资论点卡、基本面止损、事件监控、数据来源、免责声明。
- valuation：Valuation Verdict、Valuation Snapshot、公司分类、方法权重、WACC、定性调整、DCF、PE Band、DDM、交叉验证、反向估值、估值区间、数据来源、免责声明。

如果验收失败，优先修正对应报告 prompt/template，而不是放宽验收规则。
```

- [ ] **Step 4: Run README test**

Run:

```bash
python -m pytest tests/test_validate_reports.py::test_readme_documents_report_validator -v
```

Expected: PASS.

- [ ] **Step 5: Run focused test suite**

Run:

```bash
python -m pytest tests/test_report_schema.py tests/test_validate_reports.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit documentation task**

Run:

```bash
git add README.md tests/test_validate_reports.py
git commit -m "docs: document three report validation"
```

Expected: commit succeeds.

---

### Task 5: Final Verification

**Files:**
- No new files unless a prior task uncovered a bug.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_report_schema.py tests/test_validate_reports.py -v
```

Expected: PASS.

- [ ] **Step 2: Run existing non-integration tests**

Run:

```bash
python -m pytest tests -m "not integration" -v
```

Expected: PASS. If unrelated legacy tests fail, record exact failures and do not broaden this task.

- [ ] **Step 3: Run validator on known samples**

Run:

```bash
python scripts/validate_reports.py output/000538_acceptance
python scripts/validate_reports.py output/603288_runner_repro
```

Expected: These may fail if current reports do not yet match the stricter target schema. Capture missing items as the backlog for the next plan: prompt/template alignment.

- [ ] **Step 4: Inspect git status**

Run:

```bash
git status --short
```

Expected: clean working tree if all commits were created. If uncommitted files remain, inspect and either commit relevant files or report them.

---

## Self-Review

- Spec coverage: The plan implements a shared finished-report schema, separate qualitative/turtle/valuation schemas, Markdown validation, output directory validation, README usage, and sample validation. It deliberately defers prompt/HTML/runner changes to later because those are separate subsystems.
- Placeholder scan: No TBD/TODO/fill-later steps remain. All code steps contain concrete code.
- Type consistency: `ReportSchema`, `SchemaRequirement`, `REPORT_SCHEMAS`, `ValidationResult`, `validate_markdown`, `validate_file`, and `validate_output_dir` are introduced before use and referenced consistently.
- Scope check: This plan is focused on schema + validator only. It does not attempt to rewrite report generation, which should be the next plan after validator results reveal exact template gaps.
