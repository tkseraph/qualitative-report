from pathlib import Path
import subprocess

import pytest

from wechat_report import (
    build_wxgzh_command,
    discover_report,
    infer_report_type,
    main,
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
