from pathlib import Path

from build_data_pack_report import build_report


DATA_PACK_MARKET = """
# 数据包

| 字段 | 值 |
| --- | --- |
| 公司名称 | 万华化学 |
| 股票代码 | 600309.SH |
"""


SECTIONS = {
    "P13": "--- p.8 ---\n九、非经常性损益项目及金额\n合计 383,528,008.36 100,000,000.00 200,000,000.00 --",
    "P4": "--- p.208 ---\n烟台东方威思顿电气有限公司 同受国丰集团控制\n冰轮环境技术股份有限公司 同受国丰集团控制",
    "P6": "--- p.213 ---\n资产负债表日不存在重要承诺事项。",
    "SUB": "--- p.187 ---\n万华化学（福建）能源科技有限公司 制造业 注销\n万华化学集团（蓬莱）储运有限公司 服务业 设立\n烟台万禾香料有限公司 制造业 设立",
    "P3": "--- p.123 ---\n按账龄披露\n1年以内（含1年） 15,562,340,000.00 12,000,000,000.00\n合计 16,842,153,127.84 12,500,000,000.00",
}


def test_report_pack_does_not_emit_unrelated_company_entities():
    report = build_report(Path("output/600309_wanhua_e2e_fresh"), DATA_PACK_MARKET, SECTIONS)

    assert "云南白药" not in report
    assert "云南省医药" not in report
    assert "云白国际" not in report
    assert "上海医药" not in report
    assert "新华都" not in report
    assert "万华化学（福建）能源科技有限公司" in report


def test_report_pack_cleans_markdown_table_entity_rows():
    sections = dict(SECTIONS)
    sections["P4"] = """
--- p.217 ---
| 上海融和电科融资租赁有限公司及其部分子公司 | 联营企业 |
| 上海杉杉锂电材料科技有限公司部分子公司 | 联营企业 |
"""
    report = build_report(Path("output/300750_catl_e2e_fresh"), DATA_PACK_MARKET, sections)

    assert "| 上海融和电科融资租赁有限公司及其部分子公司 | 联营企业 | — | 治理观察对象 |" in report
    assert "| | 上海融和" not in report


def test_report_pack_keeps_p3_found_but_marks_empty_aging_rows_as_unavailable():
    sections = dict(SECTIONS)
    sections["P3"] = """
--- p.165 ---
| 银行存款 | 305,992,667 | 274,816,769 |
| 合计 | 333,512,927 | 303,511,993 |
"""
    report = build_report(Path("output/300750_catl_e2e_fresh"), DATA_PACK_MARKET, sections)

    assert "| 状态 | P3 已命中，但未提取到稳定账龄明细 |" in report
    assert "| 账龄 | 期末账面余额（元） | 期初账面余额（元） |" not in report
