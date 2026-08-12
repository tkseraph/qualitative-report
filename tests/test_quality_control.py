"""Tests for deterministic qualitative-report metric budgeting."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from quality_control import (
    build_report,
    main,
    parse_matrix,
    parse_sections,
    payout_ratio,
    roe_history_summary,
    selected_working_capital_bridge,
    yoy_pct,
)


SAMPLE_PACK = """# 数据包

## 1. 基本信息
| 项目 | 内容 |
| --- | ---: |
| 股票代码 | 300628.SZ |
| 当前价格 | 50.00 |
| 总市值 (万元) | 200,000.00 |

## 3. 合并利润表
| 项目 (百万元) | 2025Q1 | 2024 | 2023 |
| --- | ---: | ---: | ---: |
| 营业收入 | 15,000 | 50,000 | 40,000 |
| 营业利润 | 3,000 | 10,000 | 8,000 |
| 净利润 | 2,500 | 9,500 | 7,500 |
| 归母净利润 | 2,400 | 10,000 | 8,000 |
| 基本EPS | 0.50 | 2.00 | 1.60 |

## 4. 合并资产负债表
| 项目 (百万元) | 2024 | 2023 |
| --- | ---: | ---: |
| 总资产 | 100,000 | 90,000 |
| 归母所有者权益 | 60,000 | 55,000 |
| 应收账款 | 20,000 | 18,000 |
| 存货 | 30,000 | 25,000 |
| 应付账款 | 15,000 | 13,000 |
| 合同负债 | 10,000 | 8,000 |

## 5. 现金流量表
| 项目 (百万元) | 2024 | 2023 |
| --- | ---: | ---: |
| 经营活动现金流(OCF) | 12,000 | 9,000 |
| 自由现金流(FCF) | 8,000 | 6,000 |

## 6. 分红历史
| 年度 | 总分红 (百万元) |
| --- | ---: |
| 2024 | 4,000 |
| 2024 | 2,000 |
| 2023 | 4,800 |

## 12. 关键财务指标
| 指标 | 2024 | 2023 |
| --- | ---: | ---: |
| ROE | 18.0 | 16.0 |
| 毛利率 | 40.0 | 38.0 |
| 净利率 | 19.0 | 18.8 |
"""


def test_metric_math_is_none_tolerant():
    assert payout_ratio(6_000, 10_000) == 60
    assert payout_ratio(1, 0) is None
    assert yoy_pct(50_000, 40_000) == 25
    assert yoy_pct(1, 0) is None


def test_roe_history_never_labels_four_years_as_five_year_average():
    four_years = roe_history_summary(
        ["2025", "2024", "2023", "2022"],
        [19.36, 24.81, 51.01, 62.67],
    )
    assert four_years["n"] == 4
    assert four_years["available_mean"] == pytest.approx(39.4625)
    assert four_years["five_year_mean"] is None


def test_working_capital_bridge_treats_contract_liability_as_financing():
    sections = parse_sections(SAMPLE_PACK)
    years, balance = parse_matrix(sections["4"])
    bridge = selected_working_capital_bridge(balance, years)
    assert bridge[0]["cash_effect_proxy"] == -3_000


def test_report_ignores_quarter_and_aggregates_same_year_dividends():
    sections = parse_sections(SAMPLE_PACK)
    periods, income = parse_matrix(sections["3"])
    assert periods == ["2025Q1", "2024", "2023"]
    assert income["营业收入"]["2024"] == 50_000

    report = build_report(sections, [20], [0.9])
    assert "| 营业收入 | 50,000.00 | 500.00 | 400.00 |" in report
    assert "| 2024 | 60.00 | 100.00 | 60.00 |" in report
    assert "36.00" in report
    assert "2025Q1 百万元" not in report
    assert "roe_history_years = 2" in report
    assert "roe_5y_avg = null" in report
    assert "| 2024 vs 2023 | 20.00 | 50.00 | 20.00 | 20.00 | -30.00 |" in report
    assert "合同负债代表客户预收融资" in report


def test_cli_writes_budget_and_rejects_unparseable_input(tmp_path):
    source = tmp_path / "data_pack_market.md"
    target = tmp_path / "computed_metrics.md"
    source.write_text(SAMPLE_PACK, encoding="utf-8")
    assert main(["--input", str(source), "--output", str(target)]) == 0
    assert "CM§1" in target.read_text(encoding="utf-8")

    source.write_text("| 股票代码 | 300628.SZ |\n", encoding="utf-8")
    assert main(["--input", str(source), "--output", str(target)]) == 2


@pytest.mark.parametrize("module_mode", [False, True])
def test_direct_and_package_cli_help(module_mode):
    root = Path(__file__).resolve().parent.parent
    command = [sys.executable, "-m", "scripts.quality_control", "--help"] if module_mode else [
        sys.executable,
        "scripts/quality_control.py",
        "--help",
    ]
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    assert "computed_metrics.md" in completed.stdout
