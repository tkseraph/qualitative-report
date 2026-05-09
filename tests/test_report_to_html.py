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
