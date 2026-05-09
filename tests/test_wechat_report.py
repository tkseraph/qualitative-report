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


def test_qualitative_polish_card_values_strip_markdown_and_avoid_overcapture():
    polished = polish_qualitative_markdown(VALID_QUALITATIVE)

    quality_row = next(line for line in polished.splitlines() if line.startswith("| 商业质量 |"))
    assert "**" not in quality_row
    assert "公司依托稀缺港口区位" not in quality_row
    assert "B+ / 较强商业质量" in quality_row


def test_qualitative_polish_inserts_card_when_unrelated_project_table_exists():
    report_with_unrelated_table = VALID_QUALITATIVE + "\n\n## 附加说明\n\n| 项目 | 结论 |\n|---|---|\n| 其他事项 | 不影响首屏摘要卡 |\n"

    polished = polish_qualitative_markdown(report_with_unrelated_table)

    assert polished.count("| 公司本质 |") == 1
    assert "| 其他事项 | 不影响首屏摘要卡 |" in polished


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
