import json
from pathlib import Path

from bs4 import BeautifulSoup

from report_to_html import build_verdict, extract_kpi_cards, parse_report, render_report_html


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

## 样板证据模块

这张表用于回答收入、利润、现金、治理与叙事是否共同支持商业质量判断。

| 模块 | 核心证据 | 投资含义 |
|---|---|---|
| 收入质量拆分 | 主营港口收入稳定 | 收入质量支持基础现金流判断 |
| 利润桥 | 利润变化主要来自吞吐量和费率 | 利润质量需要穿透可持续驱动 |
| 治理红旗 | 审计意见和关联交易未见重大异常 | 治理底线暂可接受 |

结论：样板证据模块说明评级来自多维交叉验证，而不是单一叙事。

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


SAMPLE_LEVEL_RESEARCH_MD = """
# 海螺水泥（600585.SH）— 商业模式与护城河定性分析

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 强周期重资产水泥龙头 |
| 商业质量 | 中等偏上 |
| 护城河来源 | 成本、规模、矿山和物流 |
| 最大风险 | 需求下台阶与 ROE 低位 |
| 反证条件 | ROE 长期低于资本成本 |

## 自适应研究计划

| 项目 | 判断 | 证据路径 | 反证重点 |
|---|---|---|---|
| 公司类型 | 强周期重资产 | 吨价、吨成本、Capex、D&A、FCF | 成本红利不可持续 |
| 核心质量问题 | 成本优势能否转化为 ROE | 周期轨迹、利润桥、现金转化 | 需求下台阶 |

## Executive Summary / 执行摘要

海螺的关键不是有没有成本优势，而是这种优势能否在需求下台阶后转化为资本回报。

## 交叉验证与深度分析

### 数字与叙事的匹配

| 叙事 | 财务验证 | 冲突 / 反证 |
|---|---|---|
| 成本优势 | 吨成本下降 | 价格仍弱 |

### 核心矛盾

- 吨毛利改善 vs 行业内卷。

### 被忽视信号

- 资产减值损失、研发费用、投资收益和口径差异需要单独复核。

## 未来观察变量

| 指标 | 当前值 | 阈值 |
|---|---|---|
| 吨成本 | 166 元/吨 | 高于 180 元/吨 |

## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| moat_rating | 中 |
"""


def test_parse_report_extracts_upgraded_qualitative_sections():
    report = parse_report(QUALITATIVE_WITH_POLISH_SECTIONS)

    assert "项目" in report["first_screen_card"]
    assert "核心矛盾" in report["core_contradiction"]
    assert "收入质量拆分" in report["evidence_modules"]
    assert "触发后的重评动作" in report["future_observations"]
    assert "moat_rating" in report["parameters_table"]
    assert report["conclusion"]
    assert len(report["dimensions"]) == 1


def test_parse_report_extracts_sample_level_research_sections():
    report = parse_report(SAMPLE_LEVEL_RESEARCH_MD)

    assert "公司类型" in report["adaptive_research_plan"]
    assert "证据路径" in report["adaptive_research_plan"]
    assert "数字与叙事的匹配" in report["cross_validation_research"]
    assert "核心矛盾" in report["cross_validation_research"]
    assert "被忽视信号" in report["cross_validation_research"]
    assert "###" not in report["cross_validation_research"]
    assert "<h3>数字与叙事的匹配</h3>" in report["cross_validation_research"]
    assert "<h3>核心矛盾</h3>" in report["cross_validation_research"]



def test_parse_report_extracts_h3_deep_summary_as_conclusion():
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
### 深度总结 / 核心投资逻辑

公司本质是强周期重资产龙头，优势来自成本与规模，但反证条件是 ROE 长期低于资本成本。
"""

    report = parse_report(md_text)

    assert report["conclusion"]
    assert "强周期重资产龙头" in report["conclusion"]


def test_parse_report_extracts_company_metadata_without_title_dash():
    md_text = """# 海螺水泥（600585.SH）商业模式与护城河定性分析

> 分析日期：2026-05-18

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 强周期重资产水泥龙头 |
"""

    report = parse_report(md_text)

    assert report["company_name"] == "海螺水泥"
    assert report["stock_code"] == "600585.SH"


def test_parse_report_extracts_company_metadata_from_quality_assessment_title():
    md_text = """# 万泽股份（000534.SZ）商业质量评估报告

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 双主业平台 |
"""

    report = parse_report(md_text)

    assert report["company_name"] == "万泽股份"
    assert report["stock_code"] == "000534.SZ"



def test_parse_report_accepts_d_numbered_dimension_headings():
    d_numbered = QUALITATIVE_WITH_POLISH_SECTIONS.replace(
        "## 维度一：商业模式与资本特征",
        "## D1. 商业模式与资本特征",
    )

    report = parse_report(d_numbered)

    assert len(report["dimensions"]) == 1
    assert report["dimensions"][0]["title"] == "D1. 商业模式与资本特征"


def test_parse_report_extracts_dimension_badges_from_reader_facing_status_lines():
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

本章评级：**强**。资本效率优秀。

## 维度二：竞争优势与护城河

竞争优势评价：**中**。优势存在但周期扰动明显。

## 维度三：外部环境与周期位置

周期状态：**风险观察**。价格仍在底部区间。

## 维度四：管理层与治理

治理评价：**反证触发**。若出现资金占用则下调。
"""

    report = parse_report(md_text)

    assert [dimension["badge"] for dimension in report["dimensions"]] == ["强", "中", "风险观察", "反证触发"]
    assert [dimension["badge_class"] for dimension in report["dimensions"]] == [
        "badge-strong",
        "badge-medium",
        "badge-medium",
        "badge-weak",
    ]


def test_render_report_html_promotes_dimension_summary_lists_to_cards(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 本章小结

- 本章结论：重资产但现金流韧性较强。
- 最重要证据：OCF 连续为正且 Capex/D&A 回落。
- 观察风险 / 重评触发：若 FCF 再次转负，需要下调资本质量。

后续正文继续展开经营杠杆。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "dimension-summary-grid" in html
    assert "dimension-summary-card" in html
    assert "本章结论" in html
    assert "最重要证据" in html
    assert "观察风险 / 重评触发" in html
    assert "重资产但现金流韧性较强" in html
    assert "OCF 连续为正" in html
    assert "后续正文继续展开经营杠杆" in html



def test_render_report_html_promotes_plain_dimension_summary_lines_to_cards(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 本章小结

本章结论：D1 评级为**较强但重资产约束明显**。

最重要证据：完全成本约 12 元/kg、2025 年 FCF 约 205.27 亿元。

观察风险 / 重评触发：若 FCF 再度转负，应下调资本质量。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "dimension-summary-grid" in html
    assert html.count("dimension-summary-card") == 3
    assert "较强但重资产约束明显" in html
    assert "完全成本约 12 元/kg" in html
    assert "若 FCF 再度转负" in html



def test_render_report_html_decorates_reader_facing_status_terms(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

风险状态：风险观察。若 FCF 转负则反证触发并下调评级。

| 检查项 | 状态 | 动作 |
|---|---|---|
| 现金流 | 正面 | 继续观察 |
| 周期压力 | 中性 | 等待验证 |
| 治理红旗 | 负面 | 下调 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert '<span class="status-tag status-positive">正面</span>' in html
    assert '<span class="status-tag status-neutral">中性</span>' in html
    assert '<span class="status-tag status-negative">负面</span>' in html
    assert '<span class="status-tag status-watch">风险观察</span>' in html
    assert '<span class="status-tag status-negative">反证触发</span>' in html
    assert '<span class="status-tag status-negative">红旗</span>' in html
    assert '<span class="status-tag status-negative">下调</span>' in html



def test_render_report_html_demotes_limitations_to_collapsible_appendix_panel(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 报告局限与数据警示

| 类型 | 当前限制 | 后续复核 |
|---|---|---|
| 同业数据缺口 | 部分同业 2025 年口径不同 | 年报披露后复核 |

局限不推翻评级，但需要持续复核。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert '<section class="research-article-section report-limitations-section">' not in html
    assert '<h2>报告局限与数据警示</h2>' not in html
    assert '<details class="appendix-panel report-limitations-panel">' in html
    assert '<summary>Appendix · 报告局限与数据警示</summary>' in html
    assert "同业数据缺口" in html
    assert "局限不推翻评级" in html



def test_render_report_html_writes_sample_level_visual_sections(tmp_path):
    report_path = tmp_path / "600018_SH_qualitative_report.polished.md"
    output_path = tmp_path / "600018_SH_qualitative_report.preview.html"
    report_path.write_text(QUALITATIVE_WITH_POLISH_SECTIONS, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "sample-hero" in html
    assert "snapshot-grid" in html
    assert "executive-summary-card" in html
    assert "evidence-modules-section" not in html
    assert "<h2>证据模块</h2>" not in html
    assert "dimension-card" in html
    assert "observation-panel" in html
    assert "appendix-panel" in html
    assert "report-disclaimer" in html


def test_render_report_html_writes_sample_level_research_panels(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "adaptive-research-section" not in html
    assert "<h2>自适应研究计划</h2>" not in html
    assert "cross-validation-panel" in html
    assert "交叉验证与深度分析" in html
    assert "被忽视信号" in html


def test_render_report_html_omits_site_navigation_chrome(tmp_path):
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "Terance Jiang" not in html
    assert "site-nav" not in html
    assert "nav-logo" not in html
    assert "个股研究" not in html
    assert "投资随想" not in html
    assert "行业分析" not in html



def test_render_report_html_promotes_cross_validation_reassessment_matrix(tmp_path):
    md_text = """
# 测试公司（600000.SH）— 商业模式与护城河定性分析

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 测试公司 |
| 商业质量 | 中等 |
| 护城河来源 | 渠道与客户认证 |
| 最大风险 | 现金转化下滑 |
| 反证条件 | 应收恶化 |

## Executive Summary / 执行摘要

摘要。

## 交叉验证与深度分析

### 评级复判表

| 复判项 | 证据 | 解释 | 评级动作 |
|---|---|---|---|
| 支持当前评级的证据 | ROE 仍高于同业 | 护城河仍有部分证据 | 维持 |
| 削弱当前评级的证据 | 应收和存货占用上升 | 现金质量削弱商业质量 | 观察 |
| 证据冲突的解释 | 盈利能力强但现金转化变弱 | 评级不应上调 | 观察 |
| 触发重评的最小变量 | OCF/净利润低于 0.8 | 触发下调复核 | 下调 |
"""
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "cross-reassessment-grid" in html
    assert "cross-reassessment-card support-card" in html
    assert "cross-reassessment-card pressure-card" in html
    assert "cross-reassessment-card conflict-card" in html
    assert "cross-reassessment-card trigger-card" in html
    assert "评级动作" in html
    assert "OCF/净利润低于 0.8" in html



def test_render_report_html_marks_first_screen_and_dimension_semantic_panels(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 利润桥重算

读图结论：利润桥要拆开毛利、费用、投资收益和非经营项，才能判断可持续利润。

| 利润桥环节 | 当前证据 | 质量判断 | 重评动作 |
|---|---|---|---|
| 毛利 | 成本下降支撑毛利修复 | 正面 | 跟踪吨成本 |
| 费用 | 管理费用和财务费用保持可控 | 中性 | 复核费用率 |

投资含义是利润修复必须落到可持续利润，而不是只看报表利润。

## 维度二：竞争优势与护城河

### 护城河六步审讯链

护城河必须先拆行业地图和优势来源，再看反证与同业坐标。

| 审讯环节 | 当前证据 | 反向检验 | 投资含义 |
|---|---|---|---|
| 行业地图 | 区域格局稳定 | 新进入者扩产 | 先看结构 |
| 竞争对标 | 同业 ROE 较低 | 同业修复更快 | 复核相对强弱 |

投资含义是护城河要经得起同业和 KPI 反证。

## 维度四：管理层与治理

### 治理红旗排雷清单

治理先排雷，再讨论资本配置是否加分。

| 红旗项 | 当前证据 | 异常阈值 | 重评动作 |
|---|---|---|---|
| 审计意见 | 标准无保留 | 非标意见 | 下调治理评价 |
| 资金占用 | 未见非经营占用 | 控股股东占用 | 触发红旗 |

投资含义是红旗项会直接影响管理层可信度。

## 维度五：MD&A 解读

### MD&A 审讯表

MD&A 不能只复述管理层说法，必须逐条追问兑现情况。

| 管理层原始说法 | 财务验证 | 实际兑现 | 风险措辞变化 | 沉默信息 | 下一年复核指标 |
|---|---|---|---|---|---|
| 成本优势 | 毛利率修复 | 部分兑现 | 需求风险仍在 | 价格弹性不足 | 吨成本 |

投资含义是叙事必须被财务结果验证。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "first-screen-thesis-card" in html
    assert "semantic-panel-heading profit-bridge-panel" in html
    assert "semantic-panel-heading moat-interrogation-panel" in html
    assert "semantic-panel-heading governance-red-flag-panel" in html
    assert "semantic-panel-heading mda-interrogation-panel" in html


def test_render_report_html_normalizes_awkward_investment_implication_prefix(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度二：竞争优势与护城河

### 护城河复判

投资含义是：护城河可以给“中等偏强”，但不能给“强”，因为资本回报证据还不够硬。
"""
    report_path = tmp_path / "600378_SH_qualitative_report.md"
    output_path = tmp_path / "600378_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "投资含义是：" not in html
    assert "投资含义：护城河可以给“中等偏强”，但不能给“强”" in html


def test_render_report_html_marks_reader_facing_profit_recast_heading(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 核心经营利润重算显示评级仍成立

读图结论：报表利润需要剔除投资收益、非经常性损益和一次性因素后再看可持续性。

| 利润桥步骤 | 金额 | 计算依据或计算口径 | 质量判断 |
|---|---:|---|---|
| 报表利润 | 81.13 | 年报披露 | 起点可用 |
| 核心经营利润重算 | 76.46 | 剔除非经营项 | 评级仍成立 |

投资含义是可持续利润仍支撑当前评级。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "semantic-panel-heading profit-bridge-panel" in html


def test_render_report_html_promotes_first_screen_thesis_hierarchy(tmp_path):
    md_text = """
# 牧原股份（002714.SZ）— 商业模式与护城河定性分析

## Business Quality Verdict / 商业质量总体评级

| 项目 | 结论 |
|---|---|
| 公司本质 | 生猪养殖成本曲线龙头 |
| 商业质量 | B+ / 较强 |
| 护城河来源 | 成本、规模、育种和一体化管理 |
| 最大风险 | 猪周期下行和资本开支反噬 |
| 反证条件 | 完全成本连续两年高于同业或 FCF 再次转负 |

一句话结论：**牧原是强周期养殖龙头，当前评级依赖成本优势穿越周期。**

## Executive Summary / 执行摘要

牧原的关键不是规模最大，而是成本优势是否能在猪周期下行时留下现金。

## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| moat_rating | 较强 |
| moat_sustainability | 中等可持续 |
| cyclicality | 强周期 |
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "report-hero" in html
    assert "verdict-banner" in html
    assert "kpi-grid" in html
    assert "hero-thesis-grid" in html
    assert "hero-thesis-card hero-company-essence" in html
    assert "hero-thesis-card hero-moat-source" in html
    assert "hero-thesis-card hero-risk-card" in html
    assert "hero-thesis-card hero-refutation-card" in html
    assert "生猪养殖成本曲线龙头" in html
    assert "成本、规模、育种和一体化管理" in html


def test_render_report_html_promotes_dimension_six_sotp_tables_to_visual_cards(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度六：控股结构、子公司与 SOTP 触发

### 子公司与 SOTP 观察表

这张表用于判断集团型公司是否需要拆分估值。

| 主体 | 持股 / 口径 | 业务性质 | 价值含义 |
|---|---:|---|---|
| 中化蓝天 | 100% | 氟材料平台 | 利润贡献和周期弹性核心 |
| 昊华气体 | 控股 | 电子特气 | 高端认证资产 |
| 西北院 | 控股 | 科研院所 | 技术底座 |

### 控股网络穿透

| 层级 | 主体 | 观察重点 |
|---|---|---|
| 集团 | 中国中化 | 资源与关联交易边界 |
| 上市公司 | 昊华科技 | 资本配置与整合效率 |

## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| moat_rating | 中等偏强 |
| moat_sustainability | 中等 |
"""
    report_path = tmp_path / "600378_SH_qualitative_report.md"
    output_path = tmp_path / "600378_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "sotp-visual-panel" in html
    assert "sotp-node-grid" in html
    assert "sotp-node-card" in html
    assert "data-sotp-kind=\"subsidiary\"" in html
    assert "data-sotp-kind=\"holding-network\"" in html
    assert "中化蓝天" in html
    assert "中国中化" in html



def test_render_report_html_writes_article_rhythm_classes_for_sample_level_page(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "research-article-section" in html
    assert "section-divider" in html
    assert "report-limitations-panel" in html


def test_render_report_html_writes_trend_chart_blocks_for_multi_year_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### ROE 与利润率五年趋势

读图结论：ROE 低位说明护城河仍受周期压制。

| 年份 | ROE | 净利率 |
|---|---:|---:|
| 2021 | 19.26% | 19.8% |
| 2022 | 8.53% | 10.1% |
| 2023 | 5.65% | 7.2% |
| 2024 | 4.12% | 8.1% |
| 2025 | 4.27% | 9.5% |

### OCF / FCF / Capex 五年趋势

读图结论：FCF 是否能覆盖分红是重资产质量的关键。

| 年份 | OCF | FCF | Capex |
|---|---:|---:|---:|
| 2021 | 350 | 180 | 170 |
| 2022 | 250 | 120 | 130 |
| 2023 | 190 | 80 | 110 |
| 2024 | 160 | 60 | 100 |
| 2025 | 166 | 70 | 96 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "trend-chart-section" in html
    assert "trend-chart-card" in html
    assert "chart-container" in html
    assert "chart-caption" in html
    assert "<canvas" in html
    assert "data-chart-type" in html
    assert "data-chart-series" in html
    assert "ROE 与利润率五年趋势" in html
    assert "OCF / FCF / Capex 五年趋势" in html
    assert "读图结论" in html


def test_render_report_html_writes_chart_blocks_for_embedded_dimension_trend_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 近五年质量趋势

读图结论：ROE 低位与 Capex/D&A 回落同时出现，说明低谷修复仍需现金流验证。

| 年份 | ROE | 毛利率 | FCF | Capex/D&A |
|---|---:|---:|---:|---:|
| 2021 | 19.26% | 29.63% | 187 | 2.55 |
| 2022 | 8.53% | 21.30% | -170 | 3.92 |
| 2023 | 5.65% | 16.57% | 59 | 1.90 |
| 2024 | 4.12% | 21.70% | 72 | 1.34 |
| 2025 | 4.27% | 24.16% | 70 | 1.15 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "trend-chart-section" in html
    assert "近五年质量趋势" in html
    assert "chart-container" in html
    assert "<canvas" in html
    assert "data-chart-series" in html
    assert "drawTrendCharts" in html



def test_render_report_html_writes_chart_blocks_for_business_unit_economics_and_region_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 业务拆分

读图结论：核心业务收入占比高，但不同业务毛利率差异很大。

| 业务 | 收入 | 收入占比 | 毛利率 | 同比 |
|---|---:|---:|---:|---:|
| 42.5级水泥 | 486.27 | 58.9% | 27.22% | -7.14% |
| 32.5级水泥 | 73.98 | 9.0% | 35.59% | -12.47% |
| 熟料 | 49.41 | 6.0% | 20.80% | -1.83% |
| 骨料及机制砂 | 42.03 | 5.1% | 40.13% | -10.41% |

### 吨经济模型

读图结论：吨价下跌，但吨成本下降更快，吨毛利阶段性修复。

| 年份 | 吨价 | 吨成本 | 吨毛利 |
|---|---:|---:|---:|
| 2024 | 273.2 | 187.2 | 86.0 |
| 2025 | 258.0 | 166.4 | 91.6 |

### 区域毛利率

读图结论：海外和西部毛利率高于东部，区域结构是利润质量关键。

| 区域 | 收入 | 毛利率 | 同比变化 |
|---|---:|---:|---:|
| 东部 | 187.03 | 16.85% | -3.11 |
| 中部 | 182.88 | 29.68% | 1.08 |
| 西部 | 125.24 | 31.26% | 7.74 |
| 海外 | 58.46 | 43.31% | 10.98 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count("chart-container") >= 3
    assert "业务拆分" in html
    assert "吨经济模型" in html
    assert "区域毛利率" in html
    assert "42.5级水泥" in html
    assert "data-chart-type=\"bar-line-table\"" in html



def test_render_report_html_adds_chart_roles_units_and_mixed_bar_line_script(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 业务拆分

读图结论：核心业务收入占比高，但不同业务毛利率差异很大。

| 业务 | 收入 | 收入占比 | 毛利率 | 同比 |
|---|---:|---:|---:|---:|
| 42.5级水泥 | 486.27 | 58.9% | 27.22% | -7.14% |
| 32.5级水泥 | 73.98 | 9.0% | 35.59% | -12.47% |

### 近五年质量趋势

读图结论：ROE 与毛利率低位修复，但现金流仍需验证。

| 年份 | ROE | 毛利率 | FCF | Capex/D&A |
|---|---:|---:|---:|---:|
| 2021 | 19.26% | 29.63% | 187 | 2.55 |
| 2022 | 8.53% | 21.30% | -170 | 3.92 |
| 2023 | 5.65% | 16.57% | 59 | 1.90 |

### 资本配置流向

读图结论：资本配置用柱状图看资金流向。

| 动作 | 金额 | 占比 |
|---|---:|---:|
| Capex | 96 | 44% |
| 分红 | 72 | 33% |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "drawBarLineChart" in html
    assert "drawLineChart" in html
    assert "&quot;role&quot;: &quot;bar&quot;" in html
    assert "&quot;role&quot;: &quot;line&quot;" in html
    assert "&quot;unit&quot;: &quot;亿元&quot;" in html
    assert "&quot;unit&quot;: &quot;%&quot;" in html
    assert "&quot;unit&quot;: &quot;x&quot;" in html
    assert "data-chart-title=\"业务拆分\"" in html
    assert "data-chart-visual=\"mixed\"" in html
    assert "data-chart-visual=\"line\"" in html
    assert "data-chart-visual=\"bar\"" in html



def test_render_report_html_treats_suffix_pct_and_ratio_headers_as_lines(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 资本支出低于折旧摊销让 FCF 阶段性修复

读图结论：金额用柱状图，Capex/D&A 比率用折线图。

| 年份 | Capex_亿元 | DnA_亿元 | Capex_DnA |
|---|---:|---:|---:|
| 2023 | 150 | 100 | 1.50 |
| 2024 | 120 | 105 | 1.14 |
| 2025 | 95 | 110 | 0.86 |

### 现金转化强于净利润但应收抬升需跟踪

读图结论：OCF 和净利润用柱状图，OCF/净利润比率用折线图。

| 年份 | OCF_亿元 | 净利润_亿元 | OCF_净利润 | 应收账款_亿元 |
|---|---:|---:|---:|---:|
| 2023 | 200 | 100 | 2.0 | 40 |
| 2024 | 260 | 150 | 1.7 | 55 |
| 2025 | 452 | 155 | 2.9 | 70 |

### 分部收入显示养殖仍是利润主轴

读图结论：收入用柱状图，占比和毛利率用折线图。

| 业务 | 分部收入_亿元 | 分部收入占比_pct | 毛利率_pct |
|---|---:|---:|---:|
| 生猪 | 1200 | 82 | 18.0 |
| 屠宰肉食 | 210 | 14 | 3.0 |
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "&quot;label&quot;: &quot;Capex_DnA&quot;, &quot;values&quot;: [1.5, 1.14, 0.86], &quot;unit&quot;: &quot;x&quot;, &quot;role&quot;: &quot;line&quot;" in html
    assert "&quot;label&quot;: &quot;OCF_净利润&quot;, &quot;values&quot;: [2.0, 1.7, 2.9], &quot;unit&quot;: &quot;x&quot;, &quot;role&quot;: &quot;line&quot;" in html
    assert "&quot;label&quot;: &quot;分部收入占比_pct&quot;, &quot;values&quot;: [82.0, 14.0], &quot;unit&quot;: &quot;%&quot;, &quot;role&quot;: &quot;line&quot;" in html
    assert "&quot;label&quot;: &quot;毛利率_pct&quot;, &quot;values&quot;: [18.0, 3.0], &quot;unit&quot;: &quot;%&quot;, &quot;role&quot;: &quot;line&quot;" in html



def test_render_report_html_excludes_explanatory_columns_from_chart_series(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 核心经营利润重算显示评级仍成立

读图结论：利润桥只应画金额口径，解释、依据和质量判断不应进入图表序列。

| 利润桥步骤 | 金额 | 计算依据或计算口径 | 质量判断 |
|---|---:|---|---|
| 报表利润 | 81.13 | 2025 年报披露利润口径 | 起点可用 |
| 核心经营利润重算 | 76.46 | 剔除 12.35 亿元非经营项 | 评级仍成立 |

投资含义是利润桥图表必须服务可持续利润判断，不能把说明文字里的数字误画成数据。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"核心经营利润重算显示评级仍成立\"" in html
    assert "&quot;label&quot;: &quot;金额&quot;" in html
    assert "&quot;label&quot;: &quot;计算依据或计算口径&quot;" not in html
    assert "&quot;label&quot;: &quot;质量判断&quot;" not in html



def test_render_report_html_skips_mixed_unit_single_value_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 单位经济模型

读图结论：单位经济模型用于解释量、价、成本和现金的传导，但不同单位不能硬塞进一张图。

| 指标 | 数值 | 单位 | 投资含义 |
|---|---:|---|---|
| 出栏量 | 7477.91 | 万头 | 决定收入规模 |
| 商品猪销售均价 | 12.00 | 元/kg | 决定价格弹性 |
| 成本降幅 | 17.3 | % | 决定毛利修复 |
| 经营现金流 | 298.94 | 亿元 | 决定现金质量 |

投资含义是异质单位表应保留表格阅读，不自动生成误导性图表。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "单位经济模型" in html
    assert "data-chart-title=\"单位经济模型\"" not in html



def test_render_report_html_skips_text_heavy_unit_economics_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 单位经济模型

读图结论：单位经济表把量、价、成本和现金放在一起解释，不应从说明文字里挖数字画图。

| 指标 | 2025 证据 | 读法 |
|---|---|---|
| 出栏量 | 7798.1 万头 | 规模支撑收入，但不是利润率 |
| 经营现金流 | 452.28 亿元 | 现金改善来自 2025 年猪价与成本共振 |
| 商品猪均价 | 12.00 元/kg | 价格仍需和周期位置一起看 |
| 成本降幅 | 17.3% | 只说明成本改善，不代表需求反转 |

投资含义是这类混合单位解释表只能保留表格阅读，不能自动生成图表。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "单位经济模型" in html
    assert "data-chart-title=\"单位经济模型\"" not in html
    assert "&quot;label&quot;: &quot;读法&quot;" not in html



def test_render_report_html_rejects_ambiguous_evidence_and_explanation_series(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 核心经营利润重算显示评级仍成立

读图结论：利润桥只应画干净金额字段，金额和证据混在一起时应保留表格而不是画图。

| 利润桥步骤 | 金额 / 证据 | 解释 |
|---|---|---|
| 报表利润 | 81.13 亿元 | 2025 年报披露利润口径 |
| 投资收益 | 12.35 亿元 | 主要来自联营企业贡献，不能当经营利润 |
| 核心经营利润重算 | 76.46 亿元 | 剔除非经营项后评级仍成立 |

投资含义是利润桥图表必须使用干净金额列，不能把证据或解释列当作序列。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "核心经营利润重算显示评级仍成立" in html
    assert "data-chart-title=\"核心经营利润重算显示评级仍成立\"" not in html
    assert "&quot;label&quot;: &quot;金额 / 证据&quot;" not in html
    assert "&quot;label&quot;: &quot;解释&quot;" not in html



def test_render_report_html_does_not_chart_review_or_fulfillment_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度五：MD&A 解读

### 历史目标 vs 实际兑现

读图结论：历史目标兑现是复盘表，不应因为实际结果里含数字就自动画图。

| 年份 | 管理层目标 | 实际结果 | 读法 |
|---|---|---|---|
| 2023 | 降本增效 | 利润 42.63 亿元 | 周期低谷下仍有利润 |
| 2024 | 成本下降 | 利润 178.81 亿元 | 猪价反弹贡献更大 |
| 2025 | 成本继续下降 | 利润 154.87 亿元 | 成本改善但价格承压 |
| 2026Q1 | 延续降本 | 亏损 12.15 亿元 | 单季亏损不能画成正向金额 |

投资含义是目标兑现表用于校验叙事可信度，不是图表数据源。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "历史目标 vs 实际兑现" in html
    assert "data-chart-title=\"历史目标 vs 实际兑现\"" not in html
    assert "&quot;label&quot;: &quot;实际结果&quot;" not in html



def test_render_report_html_does_not_auto_chart_audit_judgment_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度四：管理层与治理

### 治理红旗排雷清单

读图结论：治理红旗是排雷清单，不应因为包含年份或阈值数字就自动画图。

| 红旗项 | 当前证据 | 异常阈值 | 重评动作 |
|---|---|---|---|
| 审计意见 | 2025 年标准无保留 | 非标意见 | 下调治理评价 |
| 资金占用 | 未见非经营占用 | 超过净资产 1% | 触发红旗 |

### MD&A 审讯表

读图结论：MD&A 审讯表是叙事核验，不应自动变成图表。

| 管理层原始说法 | 财务验证 | 实际兑现 | 风险措辞变化 | 沉默信息 | 下一年复核指标 |
|---|---|---|---|---|---|
| 成本优势 | 毛利率 24.16% | 部分兑现 | 需求风险仍在 | 价格弹性不足 | 吨成本 |

## 维度六：控股结构分析

### SOTP 触发决策表

读图结论：SOTP 触发表是条件判断，不应自动画图。

| 触发项 | 当前证据 | 是否展开 | 重评动作 |
|---|---|---|---|
| 子公司利润贡献 | 低于 15% | 暂不展开 | 继续观察 |

## 报告局限与数据警示

| 类型 | 当前限制 | 后续复核 |
|---|---|---|
| 同业数据缺口 | 部分同业 2025 年口径不同 | 年报披露后复核 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "治理红旗排雷清单" in html
    assert "MD&amp;A 审讯表" in html
    assert "SOTP 触发决策表" in html
    assert "报告局限与数据警示" in html
    assert "data-chart-title=\"治理红旗排雷清单\"" not in html
    assert "data-chart-title=\"MD&amp;A 审讯表\"" not in html
    assert "data-chart-title=\"SOTP 触发决策表\"" not in html
    assert "data-chart-title=\"报告局限与数据警示\"" not in html



def test_render_report_html_styles_chart_visual_grammar(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 业务拆分

读图结论：金额用柱状图，比率用折线图。

| 业务 | 收入 | 毛利率 |
|---|---:|---:|
| 水泥 | 486 | 27.2% |
| 熟料 | 49 | 20.8% |

### ROE 五年趋势

读图结论：纯比率趋势用折线图。

| 年份 | ROE | 毛利率 |
|---|---:|---:|
| 2023 | 5.65% | 16.57% |
| 2024 | 4.12% | 21.70% |
| 2025 | 4.27% | 24.16% |

### 资本配置流向

读图结论：资金流向用柱状图。

| 动作 | 金额 |
|---|---:|
| Capex | 96 |
| 分红 | 72 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert '.chart-container[data-chart-visual="mixed"]' in html
    assert '.chart-container[data-chart-visual="line"]' in html
    assert '.chart-container[data-chart-visual="bar"]' in html
    assert "data-chart-visual=\"mixed\"" in html
    assert "data-chart-visual=\"line\"" in html
    assert "data-chart-visual=\"bar\"" in html



def test_render_report_html_dispatches_bar_line_trend_to_mixed_renderer(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 收入利润ROE因果链

读图结论：收入和利润用柱状图，ROE 用折线图。

| 年份 | 收入 | 归母净利润 | ROE |
|---|---:|---:|---:|
| 2023 | 990 | 104 | 5.7% |
| 2024 | 826 | 73 | 4.1% |
| 2025 | 850 | 77 | 4.3% |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-type=\"bar-line-trend\"" in html
    assert "data-chart-visual=\"mixed\"" in html


def test_render_report_html_adds_mobile_chart_and_table_readability_contract(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 图表六：同业质量坐标

chart_ready: true; chart_id: mobile-peer; chart_target: dimension_1; chart_type: mixed; x_axis: 公司; bar_series: 营业收入; line_series: 销售毛利率,加权ROE; unit_map: 营业收入=亿元,销售毛利率=%,加权ROE=%

读图结论：移动端图表保留趋势，精确数值由可横向滚动的数据表承载。

| 同业公司 | 营业收入 | 销售毛利率 | 加权ROE |
|---|---:|---:|---:|
| 益坤电气股份 | 3.73 | 32.23 | 18.65 |
| 神马电力股份 | 17.21 | 46.18 | 24.28 |
"""
    report_path = tmp_path / "920222_BJ_qualitative_report.md"
    output_path = tmp_path / "920222_BJ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    chart = soup.select_one('.chart-container[data-chart-id="mobile-peer"]')
    assert chart is not None
    assert chart["data-mobile-density"] == "reduced"
    assert chart["data-mobile-value-labels"] == "collision-aware-complete"
    assert chart["data-mobile-category-labels"] == "complete"
    assert chart["data-mobile-chart-scroll"] == "responsive-wide"
    assert len(soup.select('.chart-table-region[data-mobile-table="scroll"]')) >= 1
    assert soup.select_one('meta[name="qualitative-mobile-contract"]')["content"] == "2.2"
    assert "height:286px" in html
    assert "横向滑动查看完整数据" in html
    assert "var compact = width <= 620 || mobileMedia.matches" in html
    assert "window.matchMedia('(max-width: 700px)')" in html
    assert "formatCompactValue" in html
    assert "compactUnit" in html
    assert "compactValueFont" in html
    assert "mobileChartMinWidth" in html
    assert "--mobile-chart-width" in html
    assert "横向滑动查看完整图表" in html
    assert "valueLabelPriority" in html
    assert "var seriesXOffset = role === 'line'" in html
    assert "(datasets.length - 1) / 2) * 18" in html
    assert "index === ds.values.length - 1 ? 1000" in html
    assert "function drawValueLabels(ctx, datasets, x, y, role, occupiedLabelRects, compact, colorOffset, pad, width, height){\n    if (compact) return" not in html
    assert "compact ? drawValueLabels(ctx, lineDatasets, x, y, 'line'" in html
    assert "drawValueLabels(ctx, barSets, barLabelX, y, 'bar', [], compact" in html
    assert "compactCategoryLabel" in html
    assert "compactCategoryLines" not in html
    assert "compactLabelIndexes" not in html
    assert "if (!visible[i]) return" not in html
    assert "if (!placed && compact && bestPlacement)" in html
    assert "overlapPenalty" in html
    assert "drawValueLabelText" in html
    assert "strokeText" in html
    assert "mobileValueLabelsDrawn" in html
    assert "mobileValueLabelsExpected" in html
    assert "mobileCategoryLabelsDrawn" in html
    assert "mobileCategoryLabelsExpected" in html
    assert "position:sticky;left:0" in html
    assert "window.addEventListener('resize'" in html
    assert "container.dataset.chartType === 'bar-line-trend'" in html
    assert "drawBarLineChart(canvas, payload)" in html
    assert "var lineSets = payload.datasets.filter(function(ds){ return ds.role !== 'bar'; });" in html
    assert "filter(function(ds){ return ds.role !== 'bar'; }).slice(0, 3)" not in html



def test_render_report_html_uses_reader_facing_axis_unit_labels(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 资本开支与折旧摊销验证

读图结论：金额用柱状图，Capex/D&A 比率用折线图。

| 年份 | Capex_亿元 | Capex_DnA |
|---|---:|---:|
| 2023 | 150 | 1.50 |
| 2024 | 120 | 1.14 |
| 2025 | 95 | 0.86 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "左轴 " not in html
    assert "右轴 " not in html
    assert "金额 · 亿元" in html
    assert "比率 · 倍" in html



def test_render_report_html_uses_collision_aware_value_labels_for_dense_mixed_charts(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度二：竞争优势与护城河

### 图表六：同业对比显示规模优势真实，但负债和 ROE 限制护城河评级

读图结论：多组柱线组合需要避免数值标签互相覆盖。

| 公司 | 收入 | FCF | 毛利率 | ROE | 资产负债率 |
|---|---:|---:|---:|---:|---:|
| 浙江龙盛集团 | 133.13 | 55.65 | 30.20 | 5.46 | 56.26 |
| 闰土股份 | 57.30 | 6.00 | 19.43 | 6.93 | 11.81 |
| 安诺其股份 | 10.06 | -0.82 | 8.58 | -2.52 | 29.11 |
| 吉华集团 | 15.24 | 0.36 | 12.43 | 1.39 | 13.07 |
"""
    report_path = tmp_path / "600352_SH_qualitative_report.md"
    output_path = tmp_path / "600352_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "function rectsOverlap" in html
    assert "function shouldDrawValueLabel" in html
    assert "occupiedLabelRects" in html
    assert "drawValueLabels(ctx, barSets, barLabelX, barY, 'bar', occupiedLabelRects, compact, 0, pad, width, height)" in html
    assert "drawValueLabels(ctx, lineSets, lineX, lineY, 'line', occupiedLabelRects, compact, barSets.length, pad, width, height)" in html



def test_render_report_html_positions_mixed_amount_and_ratio_labels_on_separate_axes(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 资本开支与折旧摊销验证

读图结论：Capex 金额用左轴柱状图，Capex/D&A 比率用右轴折线图，标签不能互相挤压。

| 年份 | Capex_亿元 | Capex_DnA |
|---|---:|---:|
| 2023 | 150 | 1.50 |
| 2024 | 120 | 1.14 |
| 2025 | 95 | 0.86 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-visual=\"mixed\"" in html
    assert "drawAxisMaxLabels(ctx, width, pad, barRange, lineRange, barSets[0], lineSets[0], compact)" in html
    assert "drawValueLabels(ctx, barSets, barLabelX, barY, 'bar', occupiedLabelRects, compact, 0, pad, width, height)" in html
    assert "drawValueLabels(ctx, lineSets, lineX, lineY, 'line', occupiedLabelRects, compact, barSets.length, pad, width, height)" in html
    assert ": {left: 58, right: 58, top: 28, bottom: 38}" in html



def test_render_report_html_skips_overwide_mixed_causal_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度三：外部环境与周期

### 需求、价格、成本、ROE 与 FCF 的同线验证

读图结论：这张表同时混入需求、价格、成本、盈利率、资本回报和现金流，应拆成更小的样板式图表而不是自动画成一张大杂烩图。

| 年份 | 需求 / 销量 | 价格 | 成本 | 毛利率 | ROE | FCF |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 4026 | 18.7 | 16.0 | 16.6% | 23.6% | -95 |
| 2022 | 6120 | 19.2 | 15.7 | 18.3% | 18.8% | -72 |
| 2023 | 6382 | 15.0 | 14.7 | 12.0% | 4.2% | -5 |
| 2024 | 7160 | 16.0 | 13.0 | 18.7% | 17.8% | 299 |
| 2025 | 7798 | 14.5 | 12.0 | 16.6% | 15.8% | 452 |

投资含义是 D3 因果链应该拆成价格成本剪刀差、ROE 趋势和现金质量图，而不是塞进同一张图。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "需求、价格、成本、ROE 与 FCF 的同线验证" in html
    assert "data-chart-title=\"需求、价格、成本、ROE 与 FCF 的同线验证\"" not in html



def test_render_report_html_uses_only_explicit_numbered_core_charts_when_present(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 图表一：收入和利润修复仍带有强周期放大

读图结论：收入和利润用柱状图，净利率用折线图。

| 年份 | 营业收入_亿元 | 归母净利润_亿元 | 净利率_pct |
|---|---:|---:|---:|
| 2023 | 1108 | -43 | -3.9 |
| 2024 | 1379 | 178 | 12.9 |
| 2025 | 1402 | 155 | 11.0 |

### 图表二：分部收入显示养殖仍是利润主轴

读图结论：收入用柱状图，占比用折线图。

| 业务 | 分部收入_亿元 | 分部收入占比_pct |
|---|---:|---:|
| 生猪 | 1200 | 86 |
| 屠宰肉食 | 180 | 13 |

### 图表三：资本开支低于折旧摊销让 FCF 阶段性修复

读图结论：Capex 和 D&A 用柱状图，Capex/D&A 用折线图。

| 年份 | Capex_亿元 | DnA_亿元 | Capex_DnA |
|---|---:|---:|---:|
| 2023 | 151 | 100 | 1.51 |
| 2024 | 120 | 105 | 1.14 |
| 2025 | 95 | 110 | 0.86 |

### 图表四：现金转化强于净利润但应收抬升需跟踪

读图结论：现金和应收用柱状图，OCF/净利润用折线图。

| 年份 | OCF_亿元 | 净利润_亿元 | OCF_净利润 | 应收账款_亿元 |
|---|---:|---:|---:|---:|
| 2023 | 200 | -43 | -4.7 | 40 |
| 2024 | 260 | 178 | 1.5 | 55 |
| 2025 | 452 | 155 | 2.9 | 70 |

### 图表五：近五年质量趋势显示 ROE 不是平滑复利

读图结论：ROE 和毛利率用折线图。

| 年份 | ROE_pct | 毛利率_pct | FCF_亿元 |
|---|---:|---:|---:|
| 2023 | -4.2 | 12.0 | -5 |
| 2024 | 17.8 | 18.7 | 299 |
| 2025 | 15.8 | 16.6 | 452 |

### 图表六：同业对比证明规模和效率领先

读图结论：收入和销量用柱状图，毛利率和 ROE 用折线图。

| 公司 | 收入_亿元 | 生猪销量_万头 | 毛利率_pct | ROE_pct |
|---|---:|---:|---:|---:|
| 牧原股份 | 1402 | 7798 | 16.6 | 15.8 |
| 温氏股份 | 1000 | 3302 | 13.0 | 11.0 |

## 维度一：商业模式与资本特征

### 核心经营利润重算显示评级仍成立

读图结论：这张表是利润复核表，不应在已有六张核心图时额外进入图表区。

| 利润桥项目 | 金额_亿元 |
|---|---:|
| 报表归母净利润 | 155 |
| 核心经营利润 | 148 |

### 近五年质量趋势说明周期弹性

读图结论：这张表是维度内复核，不应重复进入图表区。

| 年份 | ROE | 毛利率 | FCF |
|---|---:|---:|---:|
| 2023 | -4.2% | 12.0% | -5 |
| 2024 | 17.8% | 18.7% | 299 |
| 2025 | 15.8% | 16.6% | 452 |
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count("data-chart-title=\"图表") == 6
    assert "data-chart-title=\"核心经营利润重算显示评级仍成立\"" not in html
    assert "data-chart-title=\"近五年质量趋势说明周期弹性\"" not in html



def test_render_report_html_removes_executive_chart_ready_blocks_from_summary_body(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## Executive Summary / 执行摘要

昊华科技的利润修复需要和 ROE 同时看。

### 图表一：利润修复还没有把 ROE 拉回历史高位

chart_ready: true; chart_type: mixed; x_axis: 年份; bar_series: 收入,归母净利润; line_series: ROE; unit_map: 收入=亿元, 归母净利润=亿元, ROE=%

读图结论：收入和利润用柱状图，ROE 用折线图。

| 年份 | 收入 | 归母净利润 | ROE |
|---|---:|---:|---:|
| 2023 | 78.52 | 9.00 | 10.75% |
| 2024 | 139.66 | 10.54 | 8.22% |
| 2025 | 166.89 | 14.44 | 8.18% |

## 维度一：商业模式与资本特征

D1 内容。
"""
    report_path = tmp_path / "600378_SH_qualitative_report.md"
    output_path = tmp_path / "600378_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "chart_ready:" not in html
    assert html.count("data-chart-title=\"图表一：利润修复还没有把 ROE 拉回历史高位\"") == 1
    assert html.count("<canvas") == 1
    assert html.count("图表一：利润修复还没有把 ROE 拉回历史高位") >= 1


def test_render_report_html_routes_numbered_chart_four_to_d1_even_with_cycle_words(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 图表四：现金转化重新接近净利润，但要防存货周期反复

chart_ready: true; chart_type: mixed; x_axis: 年份; bar_series: OCF,归母净利润,FCF; line_series: OCF/归母净利润; unit_map: OCF=亿元, 归母净利润=亿元, FCF=亿元, OCF/归母净利润=倍

读图结论：现金转化恢复是评级支撑项。

| 年份 | OCF | 归母净利润 | OCF/归母净利润 | FCF |
|---|---:|---:|---:|---:|
| 2023 | 4.75 | 3.23 | 1.47 | 2.84 |
| 2024 | 2.95 | 4.35 | 0.68 | 2.10 |
| 2025 | 3.86 | 3.94 | 0.98 | 3.41 |

## 维度三：外部环境与周期位置

D3 正文。
"""
    report_path = tmp_path / "605111_SH_qualitative_report.md"
    output_path = tmp_path / "605111_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "chart_ready:" not in html
    assert html.count("data-chart-title=\"图表四：现金转化重新接近净利润，但要防存货周期反复\"") == 1
    assert html.count("<canvas") == 1



def test_render_report_html_removes_dimension_chart_ready_blocks_from_body(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度三：外部环境与周期位置

本章判断：中性。高毛利业务仍需要验证费用和资本消耗。

### 图表五：盈利能力没有跟毛利率一样强，说明费用和资本消耗在抵消优势

chart_ready: true; chart_type: line; x_axis: 年份; bar_series: ; line_series: 毛利率,净利率,ROE; unit_map: 毛利率=%, 净利率=%, ROE=%

读图结论：毛利率长期高于 70%，但净利率和 ROE 没有同步进入强质量区间。

| 年份 | 毛利率 | 净利率 | ROE |
|---|---:|---:|---:|
| 2023 | 73.03% | 15.35% | 12.56% |
| 2024 | 74.38% | 13.95% | 11.31% |
| 2025 | 71.75% | 13.14% | 13.29% |
"""
    report_path = tmp_path / "000534_SZ_qualitative_report.md"
    output_path = tmp_path / "000534_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "chart_ready:" not in html
    assert html.count("data-chart-title=\"图表五：盈利能力没有跟毛利率一样强，说明费用和资本消耗在抵消优势\"") == 1
    assert html.count("<canvas") == 1
    assert "读图结论：毛利率长期高于 70%" in html



def test_render_report_html_embeds_explicit_core_charts_into_relevant_sections(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 图表一：收入和利润修复仍带有强周期放大

读图结论：收入和利润用柱状图，净利率用折线图。

| 年份 | 营业收入_亿元 | 归母净利润_亿元 | 净利率_pct |
|---|---:|---:|---:|
| 2023 | 1108 | -43 | -3.9 |
| 2024 | 1379 | 178 | 12.9 |
| 2025 | 1402 | 155 | 11.0 |

### 图表二：分部收入显示养殖仍是利润主轴

读图结论：收入用柱状图，占比用折线图。

| 业务 | 分部收入_亿元 | 分部收入占比_pct |
|---|---:|---:|
| 生猪 | 1200 | 86 |
| 屠宰肉食 | 180 | 13 |

### 图表三：资本开支低于折旧摊销让 FCF 阶段性修复

读图结论：Capex 和 D&A 用柱状图，Capex/D&A 用折线图。

| 年份 | Capex_亿元 | DnA_亿元 | Capex_DnA |
|---|---:|---:|---:|
| 2023 | 151 | 100 | 1.51 |
| 2024 | 120 | 105 | 1.14 |
| 2025 | 95 | 110 | 0.86 |

### 图表四：现金转化强于净利润但应收抬升需跟踪

读图结论：现金和应收用柱状图，OCF/净利润用折线图。

| 年份 | OCF_亿元 | 净利润_亿元 | OCF_净利润 | 应收账款_亿元 |
|---|---:|---:|---:|---:|
| 2023 | 200 | -43 | -4.7 | 40 |
| 2024 | 260 | 178 | 1.5 | 55 |
| 2025 | 452 | 155 | 2.9 | 70 |

### 图表五：近五年质量趋势显示 ROE 不是平滑复利

读图结论：ROE 和毛利率用折线图。

| 年份 | ROE_pct | 毛利率_pct | FCF_亿元 |
|---|---:|---:|---:|
| 2023 | -4.2 | 12.0 | -5 |
| 2024 | 17.8 | 18.7 | 299 |
| 2025 | 15.8 | 16.6 | 452 |

### 图表六：同业对比证明规模和效率领先

读图结论：收入和销量用柱状图，毛利率和 ROE 用折线图。

| 公司 | 收入_亿元 | 生猪销量_万头 | 毛利率_pct | ROE_pct |
|---|---:|---:|---:|---:|
| 牧原股份 | 1402 | 7798 | 16.6 | 15.8 |
| 温氏股份 | 1000 | 3302 | 13.0 | 11.0 |

## 维度一：商业模式与资本特征

D1 内容。

## 维度二：竞争优势与护城河

D2 内容。

## 维度三：外部环境与周期位置

D3 内容。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count('<div class="chart-container"') == 6
    assert "<h2>关键趋势图表</h2>" not in html
    assert "<section class=\"research-article-section trend-chart-section\">" not in html
    assert html.index("图表二：分部收入显示养殖仍是利润主轴") > html.index("维度一：商业模式与资本特征")
    assert html.index("图表三：资本开支低于折旧摊销让 FCF 阶段性修复") > html.index("维度一：商业模式与资本特征")
    assert html.index("图表四：现金转化强于净利润但应收抬升需跟踪") > html.index("维度一：商业模式与资本特征")
    assert html.index("图表六：同业对比证明规模和效率领先") > html.index("维度二：竞争优势与护城河")
    assert html.index("图表五：近五年质量趋势显示 ROE 不是平滑复利") > html.index("维度三：外部环境与周期位置")



def test_render_report_html_routes_numbered_charts_by_semantic_title_not_fixed_number(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 图表一：收入与利润趋势显示增长放缓

读图结论：收入和利润用柱状图，利润率用折线图。

| 年份 | 收入_亿元 | 净利润_亿元 | 净利率_pct |
|---|---:|---:|---:|
| 2023 | 50 | 10 | 20 |
| 2024 | 55 | 11 | 20 |
| 2025 | 58 | 10 | 17 |

### 图表二：产品结构显示硬件仍是收入主轴

读图结论：产品收入用柱状图，占比用折线图。

| 产品 | 收入_亿元 | 收入占比_pct |
|---|---:|---:|
| 会议终端 | 30 | 52 |
| 桌面通信 | 20 | 34 |

### 图表三：同业对比显示毛利率领先但研发效率需验证

读图结论：同业收入用柱状图，毛利率和研发率用折线图。

| 公司 | 收入_亿元 | 毛利率_pct | 研发率_pct |
|---|---:|---:|---:|
| 测试公司 | 58 | 63 | 9 |
| 同业A | 80 | 48 | 12 |

### 图表四：管理层叙事与风险措辞变化显示兑现压力

读图结论：收入增速用柱状图，存货周转和应收周转用折线图。

| 年份 | 收入增速_pct | 存货周转 | 应收周转 |
|---|---:|---:|---:|
| 2023 | 8 | 4.1 | 5.0 |
| 2024 | 5 | 3.8 | 4.6 |
| 2025 | 2 | 3.3 | 4.2 |

## 维度一：商业模式与资本特征

D1 内容。

## 维度二：竞争优势与护城河

D2 内容。

## 维度三：外部环境与周期位置

D3 内容。

## 维度四：管理层与治理

D4 内容。

## 维度五：MD&A 解读

D5 内容。
"""
    report_path = tmp_path / "300628_SZ_qualitative_report.md"
    output_path = tmp_path / "300628_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    d1 = html.index("维度一：商业模式与资本特征")
    d2 = html.index("维度二：竞争优势与护城河")
    d5 = html.index("维度五：MD&A 解读")
    assert html.index("图表二：产品结构显示硬件仍是收入主轴") > d1
    assert html.index("图表三：同业对比显示毛利率领先但研发效率需验证") > d2
    assert html.index("图表四：管理层叙事与风险措辞变化显示兑现压力") > d5
    assert html.index("图表三：同业对比显示毛利率领先但研发效率需验证") > html.index("维度二：竞争优势与护城河")
    assert html.index("图表三：同业对比显示毛利率领先但研发效率需验证") < html.index("维度三：外部环境与周期位置")



def test_render_report_html_collapses_large_dimension_tables_without_dropping_evidence(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

正文先给出判断，长表只是证据支撑，不应直接铺满阅读流。

| 年份 | 收入 | 净利润 | OCF | Capex | FCF |
|---|---:|---:|---:|---:|---:|
| 2020 | 100 | 10 | 12 | 5 | 7 |
| 2021 | 120 | 12 | 14 | 6 | 8 |
| 2022 | 130 | 11 | 13 | 7 | 6 |
| 2023 | 150 | 15 | 18 | 8 | 10 |
| 2024 | 180 | 20 | 22 | 9 | 13 |
| 2025 | 200 | 24 | 28 | 10 | 18 |

表后继续解释现金流质量。
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "正文先给出判断" in html
    assert "表后继续解释现金流质量" in html
    assert '<details class="dense-table-panel" data-component-role="dense-evidence">' in html
    assert "完整数据表" in html
    assert "<summary>" in html
    assert "2025" in html
    assert "200" in html


def test_render_report_html_opens_moat_chain_and_falsification_tables_by_default(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度二：竞争优势与护城河

### 护城河六步审讯链

| 步骤 | 审讯问题 | 事实与作用机制 | 当前结论 | 失效信号 |
|---|---|---|---|---|
| 1 | 问题一 | 机制一 | 结论一 | 信号一 |
| 2 | 问题二 | 机制二 | 结论二 | 信号二 |
| 3 | 问题三 | 机制三 | 结论三 | 信号三 |
| 4 | 问题四 | 机制四 | 结论四 | 信号四 |
| 5 | 问题五 | 机制五 | 结论五 | 信号五 |
| 6 | 问题六 | 机制六 | 结论六 | 信号六 |

### 护城河证伪表

| 支持护城河 | 削弱护城河 | 同业/竞品验证 | 可持续 KPI |
|---|---|---|---|
| 支持一 | 削弱一 | 验证一 | KPI一 |
| 支持二 | 削弱二 | 验证二 | KPI二 |
| 支持三 | 削弱三 | 验证三 | KPI三 |
| 支持四 | 削弱四 | 验证四 | KPI四 |
| 支持五 | 削弱五 | 验证五 | KPI五 |
"""
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert '<details class="dense-table-panel" data-component-role="moat-interrogation" open>' in html
    assert '<details class="dense-table-panel" data-component-role="moat-falsification" open>' in html



def test_render_report_html_dispatches_bar_table_to_bar_renderer(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 资本配置流向

读图结论：资金流向必须使用柱状图。

| 动作 | 金额 |
|---|---:|
| Capex | 96 |
| 分红 | 72 |
| 降债 | 30 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-type=\"bar-table\"" in html
    assert "data-chart-visual=\"bar\"" in html
    assert "function drawBarChart" in html
    assert "container.dataset.chartType === 'bar-table'" in html
    assert "drawBarChart(canvas, payload)" in html



def test_render_report_html_prefers_chart_ready_metadata_over_title_guess(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 资本配置流向

chart_ready: true; chart_type: line; x_axis: 年份; bar_series: ; line_series: 分红率; unit_map: 分红率=%

读图结论：这里要看分红率连续性，不能因为标题含“流向”就渲染成柱状图。

| 年份 | 分红率 |
|---|---:|
| 2023 | 30% |
| 2024 | 32% |
| 2025 | 31% |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"资本配置流向\"" in html
    assert "data-chart-type=\"multi-series-trend\"" in html
    assert "data-chart-visual=\"line\"" in html
    assert "&quot;label&quot;: &quot;分红率&quot;" in html
    assert "&quot;role&quot;: &quot;line&quot;" in html


def test_render_report_html_honors_explicit_units_and_series_roles(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 图表三：资本开支与现金占用需要放在一起观察

chart_ready: true; chart_id: explicit-units; chart_target: dimension_1; chart_type: mixed; x_axis: 年份; bar_series: Capex,D&A,应收账款; line_series: Capex/D&A; unit_map: Capex=亿元, D&A=亿元, 应收账款=亿元, Capex/D&A=倍

读图结论：金额列使用亿元，资本消耗比率使用倍数。

| 年份 | Capex | D&A | 应收账款 | Capex/D&A |
|---|---:|---:|---:|---:|
| 2024 | 1.52 | 0.33 | 2.22 | 4.63 |
| 2025 | 1.97 | 0.42 | 2.47 | 4.73 |
"""
    report_path = tmp_path / "688205_SH_qualitative_report.md"
    output_path = tmp_path / "688205_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    soup = BeautifulSoup(output_path.read_text(encoding="utf-8"), "html.parser")
    node = soup.select_one('[data-chart-id="explicit-units"]')
    assert node is not None
    payload = json.loads(node["data-chart-series"])
    datasets = {item["label"]: item for item in payload["datasets"]}
    assert datasets["D&A"]["unit"] == "亿元"
    assert datasets["应收账款"]["unit"] == "亿元"
    assert datasets["D&A"]["role"] == "bar"
    assert datasets["Capex/D&A"]["unit"] == "倍"
    assert datasets["Capex/D&A"]["role"] == "line"
    assert "sample.unit === '倍'" in output_path.read_text(encoding="utf-8")


def test_render_report_html_promotes_readout_tables_with_conclusion_titles(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 收缩式修复依赖降本而非需求反转

读图结论：利润修复来自成本和费用纪律，而不是需求反转。

| 利润桥环节 | 2025年变化 | 解释 | 质量评价 |
|---|---:|---|---|
| 营业收入 | -9.33% | 需求下行、价格承压 | 负面 |
| 毛利率 | 24.16% | 成本下降快于价格 | 正面 |
| 销售费用 | 21.0 | 渠道费用可控 | 中性 |
| 财务费用 | -6.0 | 利息收入贡献 | 正面 |

### 经营现金能覆盖低谷投入但仍受重资产约束

读图结论：OCF 仍为正，但 FCF 和 Capex/D&A 决定低谷现金质量。

| 指标 | 2025年 | 2024年 | 2023年 | 质量判断 |
|---|---:|---:|---:|---|
| OCF | 166.44 | 184.76 | 201.06 | 仍显著为正 |
| FCF | 70.00 | 72.00 | 59.00 | 能覆盖分红但弹性有限 |
| Capex/D&A | 1.15 | 1.34 | 1.90 | 资本消耗回落 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"收缩式修复依赖降本而非需求反转\"" in html
    assert "data-chart-title=\"经营现金能覆盖低谷投入但仍受重资产约束\"" in html
    assert html.count("<canvas") >= 2
    assert "&quot;label&quot;: &quot;2025年变化&quot;" in html
    assert "&quot;role&quot;: &quot;bar&quot;" in html
    assert "&quot;label&quot;: &quot;OCF&quot;" in html



def test_render_report_html_strips_readout_prefix_from_chart_titles(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 读图结论：收入质量与利润桥

读图结论：收入和利润用柱状图看规模，ROE 用折线图看资本回报是否同步修复。

| 年份 | 收入 | 归母净利润 | ROE |
|---|---:|---:|---:|
| 2021 | 1679 | 332 | 19.3% |
| 2022 | 1320 | 156 | 8.5% |
| 2023 | 990 | 104 | 5.7% |
| 2024 | 826 | 73 | 4.1% |
| 2025 | 850 | 77 | 4.3% |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"收入质量与利润桥\"" in html
    assert "data-chart-title=\"读图结论：收入质量与利润桥\"" not in html



def test_render_report_html_recognizes_peer_coordinate_tables_as_charts(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度二：竞争优势与护城河

### 同业坐标验证

读图结论：同行的毛利率、ROE 和 Capex/D&A 放在一起，才能判断优势是否只是周期差异。

| 公司 | 收入 | 毛利率 | ROE | Capex/D&A |
|---|---:|---:|---:|---:|
| 海螺水泥 | 850 | 24.2% | 4.3% | 1.15 |
| 冀东水泥 | 210 | 17.0% | 2.1% | 1.40 |
| 华新水泥 | 338 | 25.0% | 7.0% | 1.10 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"同业坐标验证\"" in html
    assert "data-chart-kind=\"bar-line\"" in html
    assert "&quot;label&quot;: &quot;收入&quot;" in html
    assert "&quot;role&quot;: &quot;bar&quot;" in html
    assert "&quot;label&quot;: &quot;ROE&quot;" in html
    assert "&quot;role&quot;: &quot;line&quot;" in html



def test_render_report_html_assigns_sample_logic_chart_kinds_and_windows(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 收入利润ROE因果链

读图结论：收入和利润用柱状图看规模，ROE 用折线图看资本回报是否同步修复。

| 年份 | 收入 | 归母净利润 | ROE |
|---|---:|---:|---:|
| 2020 | 1760 | 351 | 22.1% |
| 2021 | 1679 | 332 | 19.3% |
| 2022 | 1320 | 156 | 8.5% |
| 2023 | 990 | 104 | 5.7% |
| 2024 | 826 | 73 | 4.1% |
| 2025 | 850 | 77 | 4.3% |

### 资本配置流向

读图结论：重资产公司要看现金流先被 Capex、分红还是并购消耗。

| 动作 | 金额 | 占比 |
|---|---:|---:|
| Capex | 96 | 44% |
| 分红 | 72 | 33% |
| 并购 | 18 | 8% |
| 回购 | 0 | 0% |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "data-chart-title=\"收入利润ROE因果链\"" in html
    assert "data-chart-kind=\"bar-line\"" in html
    assert "data-chart-window=\"5y\"" in html
    assert "&quot;labels&quot;: [&quot;2021&quot;, &quot;2022&quot;, &quot;2023&quot;, &quot;2024&quot;, &quot;2025&quot;]" in html
    assert "&quot;label&quot;: &quot;收入&quot;" in html
    assert "&quot;role&quot;: &quot;bar&quot;" in html
    assert "&quot;label&quot;: &quot;ROE&quot;" in html
    assert "&quot;role&quot;: &quot;line&quot;" in html
    assert "data-chart-title=\"资本配置流向\"" in html
    assert "data-chart-kind=\"bar\"" in html
    assert "&quot;label&quot;: &quot;金额&quot;" in html



def test_render_report_html_wraps_chart_legends_to_avoid_overlap(tmp_path):
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 图表一：收入和利润修复仍带有强周期放大

读图结论：长图例必须自动换行，避免互相重叠。

| 年份 | 营业收入_亿元 | 归母净利润_亿元 | 净利率_pct | 经营现金流净额_亿元 | 应收账款周转天数_pct |
|---|---:|---:|---:|---:|---:|
| 2023 | 1108 | -43 | -3.9 | 200 | 12 |
| 2024 | 1379 | 178 | 12.9 | 260 | 15 |
| 2025 | 1402 | 155 | 11.0 | 452 | 18 |
""", encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "function drawLegend(ctx, datasets, pad, width, compact)" in html
    assert "ctx.measureText(label).width" in html
    assert "if (x !== pad.left && x + itemWidth > maxX)" in html
    assert "drawLegend(ctx, payload.datasets, pad, width, compact)" in html
    assert "drawLegend(ctx, barSets.concat(lineSets), pad, width, compact)" in html



def test_render_report_html_extracts_sample_style_year_columns_as_chart_series(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 资本消耗与现金质量

| 指标 | 2025 | 2024 | 2023 | 2022 | 2021 |
|---|---:|---:|---:|---:|---:|
| 资本支出 | 96 | 100 | 110 | 130 | 170 |
| 折旧摊销D&A | 84 | 75 | 58 | 33 | 67 |
| Capex/D&A | 1.15 | 1.34 | 1.90 | 3.92 | 2.55 |
| OCF/净利润 | 3.2 | 2.1 | 1.9 | 1.4 | 1.2 |

### 周期位置与外部变量

| 年份 | 营收 | 归母净利润 | 周期位置 |
|---|---:|---:|---|
| 2021 | 1679 | 332 | 顶部 |
| 2022 | 1320 | 156 | 顶部回落 |
| 2023 | 990 | 104 | 中段下行 |
| 2024 | 826 | 73 | 接近底部 |
| 2025 | 850 | 77 | 底部企稳 |
"""
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count("<div class=\"chart-container\"") >= 2
    assert html.count("<canvas") >= 2
    assert "data-chart-title=\"资本消耗与现金质量\"" in html
    assert "data-chart-title=\"周期位置与外部变量\"" in html
    assert "&quot;labels&quot;: [&quot;2025&quot;, &quot;2024&quot;, &quot;2023&quot;, &quot;2022&quot;, &quot;2021&quot;]" in html
    assert "&quot;label&quot;: &quot;资本支出&quot;" in html
    assert "&quot;label&quot;: &quot;Capex/D&amp;A&quot;" in html
    assert "&quot;unit&quot;: &quot;x&quot;" in html



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


def test_render_report_html_hides_process_oriented_modules_from_main_body(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 自适应研究计划

这属于生成过程，不应作为最终网页主章节裸露。

## 样板证据模块

这属于内部证据组织，不应作为最终网页主章节裸露。

## 公司类型化证据模块

这属于生成过程，不应作为最终网页主章节裸露。

## 维度一：商业模式与资本特征

D1 内容。

## 交叉验证与深度分析

综合复判内容。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "<h2>自适应研究计划</h2>" not in html
    assert "<h2>证据模块</h2>" not in html
    assert "样板证据模块" not in html
    assert "公司类型化证据模块" not in html
    assert "维度一：商业模式与资本特征" in html
    assert "交叉验证与深度分析" in html



def test_render_report_html_places_dimensions_before_late_stage_review_sections(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 核心矛盾与反证条件

核心矛盾内容。

## 自适应研究计划

研究计划内容。

## 交叉验证与深度分析

综合复判内容。

## 未来观察变量

观察变量内容。

## 报告局限与数据警示

局限内容。

## 维度一：商业模式与资本特征

D1 内容。

## 维度二：竞争优势与护城河

D2 内容。
"""
    report_path = tmp_path / "002714_SZ_qualitative_report.md"
    output_path = tmp_path / "002714_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    executive = html.index("Executive Summary")
    dimension_one = html.index("维度一：商业模式与资本特征")
    cross_validation = html.index("交叉验证与深度分析")
    future_observations = html.index("未来观察变量")
    limitations = html.index("报告局限与数据警示")
    assert executive < dimension_one
    assert dimension_one < cross_validation
    assert dimension_one < future_observations
    assert dimension_one < limitations



def test_render_report_html_writes_article_metadata_and_reading_flow_classes(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "article-meta-grid" in html
    assert "article-meta-item" in html
    assert "research-flow-index" in html
    assert "阅读路径" in html
    assert "Verdict" in html
    assert "Evidence" in html
    assert "Dimensions" in html
    assert "Risks" in html


def test_standalone_html_uses_sample_report_palette_and_typography(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    for token in (
        "--bg:#fafaf7",
        "--bg2:#f0efe9",
        "--bg3:#e8e7e0",
        "--text:#1c1c1a",
        "--text2:#5c5c58",
        "--text3:#8a8a84",
        "--accent:#1a1a18",
        "--green:#1a7a5a",
        "--green-bg:#e6f4ee",
        "--red:#c0392b",
        "--amber:#a06c1a",
        "--blue:#2563a0",
        "--purple:#6c5ce7",
        "--purple-bg:#f0eefa",
        "--cat-stock:#c0392b",
        "--cat-essay:#2563a0",
        "--cat-sector:#1a7a5a",
        "--max-width:820px",
        "--padding-x:32px",
    ):
        assert token in html
    assert "--font:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC','Microsoft YaHei',system-ui,sans-serif" in html
    assert "--mono:'JetBrains Mono','SF Mono','Fira Code',monospace" in html
    assert "--bg:#161614" in html
    assert "--green:#3dbb8a" in html
    assert "font-family:var(--font)" in html
    assert "font-family:var(--mono)" in html


def test_standalone_html_keeps_sample_style_simple_cards_and_tables(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "box-shadow:0 8px 24px" not in html
    assert "box-shadow:0 10px 28px" not in html
    assert "linear-gradient(135deg" not in html
    assert ".report-body .dimension-card{margin:34px 0;padding:0;background:transparent;border:0;border-radius:0" in html
    assert ".report-body .article-meta-item{padding:10px 12px;background:var(--bg2);border:1px solid var(--border);border-radius:8px}" in html
    assert ".report-body .research-flow-index strong{padding:3px 8px;background:var(--bg2);border:1px solid var(--border);border-radius:999px" in html


def test_render_report_html_keeps_short_core_evidence_tables_expanded(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 公司赚钱公式

| 收入来源 | 利润驱动 | 资本占用 | 现金转化 | 关键反证 |
|---|---|---|---|---|
| 主营业务 | 高毛利产品组合 | Capex 很低 | OCF 为正 | 应收恶化 |

投资含义：这张核心证据短表应该直接展开阅读。
"""
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "公司赚钱公式" in html
    assert "<td>主营业务</td>" in html
    assert "dense-table-panel" not in html
    assert "完整数据表" not in html


def test_render_report_html_still_collapses_audit_and_sotp_check_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度四：管理层与治理

### 治理红旗排雷清单

| 红旗项 | 当前证据 | 异常阈值 | 重评动作 |
|---|---|---|---|
| 审计意见 | 标准无保留 | 非标意见 | 下调治理评价 |
| 资金占用 | 未见占用 | 控股股东占用 | 触发红旗 |

## 维度六：控股结构分析

### SOTP 触发决策表

| 触发项 | 当前证据 | 是否展开 | 重评动作 |
|---|---|---|---|
| 子公司利润贡献 | 低于 15% | 暂不展开 | 继续观察 |
"""
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count("dense-table-panel") >= 2
    assert "治理红旗排雷清单" in html
    assert "SOTP 触发决策表" in html


def test_render_report_html_removes_embedded_chart_blocks_from_dimension_body(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

### 业务拆分

读图结论：收入用柱状图，毛利率用折线图。

| 业务 | 收入 | 毛利率 |
|---|---:|---:|
| 主业A | 100 | 30% |
| 主业B | 50 | 20% |

### 本章小结

- 本章结论：主业清晰。
- 最重要证据：收入和毛利率均可验证。
- 观察风险 / 重评触发：毛利率下滑。
"""
    report_path = tmp_path / "600000_SH_qualitative_report.md"
    output_path = tmp_path / "600000_SH_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert html.count("data-chart-title=\"业务拆分\"") == 1
    assert html.count("<h3>业务拆分</h3>") == 0
    assert html.count("读图结论：收入用柱状图，毛利率用折线图。") == 1
    assert html.count("<td>主业A</td>") == 1


def test_parse_report_dimension_badge_uses_short_status_not_risk_trigger_sentence():
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 维度一：商业模式与资本特征

状态词：正面，但现金转化进入风险观察。

### 本章小结

- 本章结论：商业模式清晰，资本强度低。
- 最重要证据：FCF 为正。
- 观察风险 / 重评触发：应收和存货继续快于收入增长，或 OCF/净利润连续低于 0.8。

## 维度二：竞争优势与护城河

本章评级：风险观察。

### 本章小结

- 本章结论：优势存在但需验证。
- 观察风险 / 重评触发：平台认证优势弱化、竞品降价、会议产品毛利率下滑。
"""

    report = parse_report(md_text)

    assert report["dimensions"][0]["badge"] == "正面"
    assert report["dimensions"][1]["badge"] == "风险观察"
    assert "应收" not in report["dimensions"][0]["badge"]
    assert "平台认证" not in report["dimensions"][1]["badge"]


def test_extract_kpi_cards_maps_machine_values_to_reader_facing_chinese():
    md_text = """
## 结构化参数（机器读取 / 附录）

| 参数 | 值 |
|---|---|
| capital_intensity | capital-light |
| moat_existence | true |
| cyclicality | weak-cycle |
"""

    cards = extract_kpi_cards(md_text)

    values_by_label = {card["label"]: card["value"] for card in cards}
    assert values_by_label["资本强度"] == "轻资产"
    assert values_by_label["优势存在性"] == "存在"
    assert values_by_label["周期性"] == "弱周期"


def test_render_report_html_does_not_chart_text_evidence_matrices_or_mixed_single_value_tables(tmp_path):
    md_text = SAMPLE_LEVEL_RESEARCH_MD + """
## 关键趋势图表

### 图表一：收入质量拆分与利润桥显示高毛利仍是主线

| 模块 | 亿联网络证据 | 结论 |
|---|---|---|
| 收入质量拆分 | 2025 年收入 60.33 亿元，桌面通信终端 29.71 亿元。 | 收入质量支持评级。 |
| 利润桥 | 收入 60.33 亿元，毛利约 38.20 亿元。 | 高毛利是高 ROE 来源。 |
| 现金转化 | OCF 18.32 亿元、OCF/净利润约 0.70。 | 现金质量进入观察。 |

读图结论：这是证据矩阵，不是图表数据源。

### 图表二：公司类型化证据把全球硬件公司放在同业坐标中

| 模块 | 亿联网络证据 | 反证阈值 |
|---|---|---|
| 产业坐标 | 企业通信终端和会议协作设备。 | 若平台认证弱化，产业位置下移。 |
| 同业/区域坐标 | Cisco 毛利率 64.9%，Logitech 毛利率 43.1%。 | 亿联毛利靠近普通硬件厂则下调。 |
| 反证阈值 | 毛利率 58%-60%、OCF/净利润 0.8。 | 任两项触发即重评。 |

读图结论：这是类型化证据表，不应从文字里抓数字画图。

## 维度一：商业模式与资本特征

### 资本消耗与现金创造显示轻资产优势仍被营运资本约束

读图结论：固定资产资本消耗很轻，但不同单位不能硬塞进一张图。

| 指标 | 2025 年值 | 解释 |
|---|---:|---|
| Capex | 0.53 亿元 | 维持投入很低。 |
| D&A | 0.83 亿元 | 折旧摊销高于资本开支。 |
| Capex/D&A | 0.64 | 轻资产特征明显。 |
| FCF | 17.79 亿元 | 自由现金流仍为正。 |

## 维度四：管理层与治理

### 资本配置复盘显示稳健但需剥离金融资产影响

读图结论：资本配置复盘是事项判断，不应把 2025 年当成金额。

| 动作 | 金额 | 管理层理由 | 后续结果 | 质量评价 |
|---|---:|---|---|---|
| 研发投入 | 2025 年 5.30 亿元 | 支持 AI 音视频能力。 | 主力产品毛利率保持高位。 | 正面。 |
| 分红 | 2025 年相关现金流约 22.75 亿元 | 回报股东。 | 分红友好。 | 中性偏正面。 |
| 回购 | 近三年约 1.11 亿元 | 稳定股东回报。 | 金额不大。 | 中性。 |
"""
    report_path = tmp_path / "300628_SZ_qualitative_report.md"
    output_path = tmp_path / "300628_SZ_qualitative_report.html"
    report_path.write_text(md_text, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "资本消耗与现金创造显示轻资产优势仍被营运资本约束" in html
    assert "资本配置复盘显示稳健但需剥离金融资产影响" in html
    assert "data-chart-title=\"图表一：收入质量拆分与利润桥显示高毛利仍是主线\"" not in html
    assert "data-chart-title=\"图表二：公司类型化证据把全球硬件公司放在同业坐标中\"" not in html
    assert "data-chart-title=\"资本消耗与现金创造显示轻资产优势仍被营运资本约束\"" not in html
    assert "data-chart-title=\"资本配置复盘显示稳健但需剥离金融资产影响\"" not in html
    assert "&quot;values&quot;: [2025.0" not in html


def test_extract_kpi_cards_reads_yaml_structured_parameters():
    md_text = """
## 结构化参数（机器读取 / 附录）

```yaml
schema_version: qualitative_output_schema_v1.1
D1_business_model:
  capital_intensity: capital-light
D2_moat:
  entry_barrier: 中
  roe_5y_avg: 28.64
  moat_existence: 存在
  moat_sustainability: 中等可持续
  moat_rating: 较强
D3_external_environment:
  cyclicality: 弱周期
  cycle_position: 不适用
D4_management_governance:
  management_rating: 合格
```
"""

    cards = extract_kpi_cards(md_text)

    values_by_label = {card["label"]: card["value"] for card in cards}
    assert values_by_label["5Y Avg ROE"] == "28.64"
    assert values_by_label["护城河评级"] == "较强"
    assert values_by_label["可持续性"] == "中等可持续"
    assert values_by_label["管理层评价"] == "合格"
    assert values_by_label["周期性"] == "弱周期"
    assert values_by_label["资本强度"] == "轻资产"
    assert values_by_label["进入壁垒"] == "中"
    assert values_by_label["优势存在性"] == "存在"


def test_html_verdict_and_kpi_cards_read_yaml_booleans_as_reader_facing_values():
    md_text = """
## Business Quality Verdict / 商业质量总体评级

**核心判定：海螺水泥是强周期重资产龙头，商业质量中等偏上，护城河评级为中。**

## 结构化参数（机器读取 / 附录）

```yaml
roe_5y_avg: 8.37
moat_rating: 中
moat_sustainability: 中
management_rating: 合格
cyclicality: 强周期
cycle_position: 底部磨底
capital_intensity: 重资产
entry_barrier: 中高
moat_existence: true
```
"""

    verdict = build_verdict(md_text)
    cards = extract_kpi_cards(md_text)

    assert verdict["verdict_tag"] == "MODERATE"
    assert "护城河评级 中" in verdict["verdict_text"]
    values_by_label = {card["label"]: card["value"] for card in cards}
    assert values_by_label["优势存在性"] == "存在"
    assert values_by_label["优势存在性"] != "true"


def test_html_verdict_uses_overall_business_quality_instead_of_moat_rating():
    md_text = """
## Business Quality Verdict / 商业质量总体评级

**总体评级：B+ / 中等偏强 · 观察。**

## 结构化参数（机器读取 / 附录）

```yaml
business_quality_grade: B+
business_quality_label: 中等偏强
rating_outlook: 观察
rating_version: 2.0
moat_rating: 中
moat_sustainability: 中等可持续
```
"""
    verdict = build_verdict(md_text)
    assert verdict["verdict_tag"] == "B+ / 中等偏强"
    assert verdict["verdict_tag"] != "MODERATE"
    assert "护城河评级 中" in verdict["verdict_text"]


def test_render_report_html_does_not_publish_upstream_canonical_by_default(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(report_path, output_path, standalone=True)

    html = output_path.read_text(encoding="utf-8")
    assert "terancejiang.com" not in html
    assert '<meta name="robots" content="noindex,nofollow">' in html
    assert "JetBrainsMono-Regular.woff2" not in html


def test_render_report_html_uses_explicit_published_canonical(tmp_path):
    report_path = tmp_path / "600585_SH_qualitative_report.md"
    output_path = tmp_path / "600585_SH_qualitative_report.html"
    report_path.write_text(SAMPLE_LEVEL_RESEARCH_MD, encoding="utf-8")

    render_report_html(
        report_path,
        output_path,
        standalone=True,
        base_url="https://research.example.com/",
        report_url="reports/600585-sh/qualitative/2026-05-09/",
    )

    html = output_path.read_text(encoding="utf-8")
    assert '<link rel="canonical" href="https://research.example.com/reports/600585-sh/qualitative/2026-05-09/">' in html
    assert '<meta property="og:url" content="https://research.example.com/reports/600585-sh/qualitative/2026-05-09/">' in html
