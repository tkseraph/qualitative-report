from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_qualitative_prompt_requires_finished_report_shell():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")

    required_sections = [
        "## Business Quality Verdict / 商业质量总体评级",
        "## Quality Snapshot / 质量快照",
        "## Executive Summary / 执行摘要",
        "## 未来观察变量",
        "## 数据来源",
        "## 免责声明",
        "## 结构化参数（机器读取 / 附录）",
    ]

    for section in required_sections:
        assert section in prompt


def test_turtle_report_template_requires_finished_report_shell():
    template = read_text("strategies/turtle/phase3_valuation.md")

    required_sections = [
        "## Strategy Verdict",
        "## Turtle Snapshot / 核心指标快照",
        "## Executive Summary",
        "## 数据来源与免责",
    ]

    for section in required_sections:
        assert section in template


def test_qualitative_prompt_requires_financial_sector_adjustments():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")

    assert "金融/银行/保险" in prompt
    assert "不得机械套用制造业" in prompt
    assert "净息差" in prompt
    assert "拨备覆盖率" in prompt


def test_qualitative_prompt_requires_high_rd_capex_manufacturing_assessment():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")

    assert "高研发" in prompt
    assert "高资本开支" in prompt
    assert "技术迭代" in prompt
    assert "客户议价" in prompt
    assert "自由现金流" in prompt


def test_qualitative_prompt_requires_quality_decline_and_value_trap_assessment():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")

    assert "质量下滑" in prompt
    assert "价值陷阱" in prompt
    assert "ROE 下滑" in prompt
    assert "应收账款账龄" in prompt
    assert "坏账准备" in prompt


def test_qualitative_prompt_requires_wechat_readability_long_line_guard():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    for text in (prompt, writing_style, continue_script):
        assert "正文单行" in text
        assert "100" in text
        assert "短段" in text


def test_qualitative_prompt_requires_sample_evidence_modules():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for term in (
        "收入质量拆分",
        "利润桥",
        "量价成本拆解",
        "现金转化",
        "治理红旗",
        "MD&A 叙事 vs 财务证据",
        "伪优势过滤",
        "未来观察变量",
    ):
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_generation_first_wechat_quality():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for text in (prompt, writing_style):
        assert "源报告" in text
        assert "不得依赖微信后处理" in text
        assert "公司类型化证据模块" in text
        assert "每个维度至少一组公司专属证据" in text
        assert "公司专属数字" in text


def test_qualitative_prompt_requires_type_specific_evidence_examples():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for term in (
        "轻资产公司",
        "业务线拆分",
        "费用率 / 渠道库存",
        "强周期公司",
        "单位经济模型",
        "吨价 / 吨成本 / 吨毛利",
        "重资产公司",
        "Capex/D&A",
    ):
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_dimension_argument_chains_for_wechat_style():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "D1：收入拆分 → 利润桥 → 资本消耗 → 现金质量 → 反证",
        "D2：行业地图 → ROE 验证 → 护城河来源 → 伪优势过滤 → 同业对比 → 可持续 KPI",
        "D3：周期属性 → 当前阶段 → 外部变量 → 财务敏感性 → 阈值",
        "D4：治理红旗 → 管理层/控制权 → 资本配置 → 承诺兑现",
        "D5：管理层核心叙事 → 财务验证 → 风险措辞变化 → 未解释清楚的问题 / 沉默信息",
        "D6：触发条件表 → 是否展开 → 子公司/投资收益/SOTP 判断",
        "每个维度至少一张 3-5 列窄表",
        "异常优先",
        "未解释清楚的问题 / 沉默信息",
        "触发条件表",
        "金额单位优先使用亿元或万元",
        "不要在正式报告正文中使用百万元",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_forbids_instruction_like_table_prose_in_body():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for text in (prompt, writing_style):
        assert "不得把结构说明照抄成正文" in text
        assert "这张表回答" in text
        assert "读者化结论句" in text


def test_qualitative_prompt_treats_sample_chains_as_internal_checklist_not_body_text():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for text in (prompt, writing_style):
        assert "内部写作检查清单" in text
        assert "不得把结构词" in text
        assert "表格任务说明" in text
        assert "模型指令" in text
        assert "表前" in text
        assert "表后" in text
        assert "投资含义" in text



def test_qualitative_prompt_forbids_channel_reuse_labels_in_body():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    for text in (prompt, writing_style, continue_script):
        assert "渠道用途标签" in text
        assert "微信公众号摘要可复用一句话" in text
        assert "可复用一句话" in text
        assert "可作为微信公众号摘要" in text


def test_qualitative_prompt_requires_d4_d5_d6_depth_contracts():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "D4 必须同时覆盖治理红旗、管理层/控制权、资本配置、承诺兑现",
        "D5 必须同时覆盖历史指引、实际兑现、新战略、财务验证、风险措辞变化、沉默信息、重评动作",
        "D6 必须覆盖触发条件、子公司、投资收益、SOTP 判断、阈值和计算依据",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_per_dimension_company_specific_evidence():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "每个维度至少一组公司专属证据",
        "公司专属数字、业务事实或同业对比",
        "不得只写通用框架语",
        "轻资产公司",
        "研发",
        "海外区域",
        "平台生态",
        "强周期公司",
        "周期位置",
        "外部变量",
        "重资产公司",
        "维护性投入",
        "FCF",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_d3_sensitivity_and_d6_threshold_basis():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    for text in (prompt, writing_style):
        assert "D3 必须输出周期/外部变量敏感性表" in text
        assert "当前阶段 → 外部变量 → 财务敏感性 → 预警阈值 → 重评动作" in text
        assert "阈值和计算依据" in text
        assert "投资收益、母合差异、子公司利润、非经常性损益占比" in text


def test_qualitative_prompt_requires_d6_sotp_trigger_decision_table():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "SOTP 触发决策表",
        "### SOTP 触发决策表",
        "diagnostic",
        "数据完备度",
        "最优可行分析",
        "重复计价检查",
        "子公司利润",
        "海外资产回报",
        "分部价值",
        "控股折价",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_p0_p2_sample_gap_closures():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "公司赚钱公式",
        "收入来源 → 利润驱动 → 资本占用 → 现金转化 → 关键反证",
        "护城河证伪表",
        "支持护城河的证据",
        "削弱护城河的反证",
        "管理层叙事审计表",
        "管理层说法 → 财务验证 → 是否兑现 → 沉默信息 → 重评动作",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_adaptive_research_plan_not_template_copy():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "自适应研究计划",
        "先识别公司类型、核心质量问题和关键因果链",
        "按公司逻辑选择证据",
        "不得机械照搬样板公司的细分分项",
        "证据必须服务核心判断",
        "不同公司可以使用不同证据路径",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_sample_level_research_layers():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "交叉验证",
        "数字与叙事的匹配",
        "核心矛盾",
        "被忽视信号",
        "非经营项",
        "口径差异",
        "触发比例计算",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_review_tables_and_public_output_cleanliness():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "资本配置复盘表",
        "动作 → 金额 → 管理层理由 → 后续结果 → 质量评价",
        "历史目标 vs 实际兑现表",
        "年份 → 管理层目标 → 实际结果 → 偏差 → 投资含义",
        "报告局限与数据警示",
        "不得出现本地绝对路径",
        "不得出现 WebSearch fallback",
        "不得出现 acceptance samples",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_unit_economics_and_observation_priority_tiers():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "单位经济模型",
        "销量 / 吨价 / 吨成本 / 吨毛利",
        "销量",
        "吨价",
        "吨成本",
        "吨毛利",
        "未来观察变量必须按优先级分层",
        "优先级",
        "P0",
        "P1",
        "P2",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_multi_year_trend_and_d4_d5_delivery_status():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "近五年质量趋势",
        "ROE / 毛利率 / 净利率 / FCF / Capex/D&A",
        "趋势证据",
        "多年复盘状态",
        "多年兑现状态",
        "不能只写当年事实",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_chart_ready_data_tables_and_readable_amount_columns():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "图表友好表格",
        "业务名称和金额必须拆成两列",
        "不得写成“42.5级水泥约486亿元”",
        "业务 | 收入 | 收入占比 | 毛利率 | 同比",
        "吨经济模型",
        "区域毛利率",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_adaptive_depth_not_sample_copy():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "利润桥细项",
        "毛利 / 费用 / 减值 / 投资收益 / 非经营项",
        "具名同业",
        "可比数据不可得",
        "控股股东 / 子公司 / 关联平台 / 相关上市平台",
        "读图结论",
        "金额指标优先用柱状图",
        "比率 / 毛利率 / ROE / Capex/D&A 优先用折线图",
        "3-5 年",
        "同一因果链",
        "不得硬套样板公司的图表组合",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_conclusion_title_and_canvas_density_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "标题不能只写模块名",
        "收入利润ROE因果链不能命名为“收入利润ROE因果链”",
        "单位经济模型不能命名为“单位经济模型”",
        "资本配置复盘表不能命名为“资本配置复盘表”",
        "至少 5 个可渲染图表",
        "核心图表必须优先拆成 5-6 张样板式小图",
        "收入利润趋势",
        "业务或区域收入结构",
        "资本支出 vs 折旧摊销与 Capex/D&A",
        "现金转化或 OCF/净利润与应收",
        "ROE 趋势",
        "同业规模或效率对比",
        "不得把需求、价格、成本、毛利率、ROE、FCF 全部塞进同一张图",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_html_renderer_contract_for_finished_quality():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "HTML 渲染契约",
        "图表一",
        "图表二",
        "图表三",
        "图表四",
        "图表五",
        "图表六",
        "Executive Summary 后",
        "D1 内",
        "D2 内",
        "D3 内",
        "本章结论：",
        "最重要证据：",
        "观察风险 / 重评触发：",
        "风险状态",
        "正面 / 中性 / 负面 / 风险观察 / 反证触发",
        "报告局限与数据警示作为附录材料",
    )
    for text in (prompt, writing_style):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_asset_light_tech_hardware_branch():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "轻资产科技硬件",
        "企业协作终端",
        "产品结构",
        "研发效率",
        "渠道库存",
        "平台生态",
        "兼容认证",
        "海外区域暴露",
        "现金转化",
        "技术迭代风险",
        "不强制套用吨经济或强周期价格成本链",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_single_core_quality_question_thread():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "核心商业质量问题",
        "全文必须围绕一个核心商业质量问题展开",
        "每个维度都要回扣这个问题",
        "D1：这个模式如何赚钱",
        "D2：为什么能获得超额回报",
        "D3：外部变量会不会破坏质量",
        "D4：管理层如何配置这份现金",
        "D5：管理层叙事是否解释边际变化",
        "D6：结构是否影响主业质量",
        "交叉验证：这些证据是否互相支持",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_appendix_and_framework_deemphasis_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "附录和框架说明降权",
        "报告局限、数据警示、结构化参数、分析框架与评级标准只能作为附录材料",
        "不得在 Executive Summary、D1-D6 或深度总结中解释框架定义",
        "不得把 Greenwald、护城河框架、评级标准写成主线段落",
        "正文只写公司判断、证据和投资含义",
        "附录内容不得压过 Business Quality Verdict、Executive Summary、D1-D6、交叉验证、深度总结和未来观察变量",
        "结构化参数只用于机器读取和 HTML 折叠面板",
        "分析框架说明只用于读者需要时展开阅读",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_dimension_narrative_rhythm_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "维度正文节奏",
        "判断句 → 证据模块 → 投资含义 → 本章小结",
        "每个维度第一段必须先给出本章判断",
        "证据模块不得连续堆叠超过两张表",
        "每个核心表格后必须回扣核心商业质量问题",
        "本章小结必须压缩为本章结论、最重要证据、观察风险 / 重评触发",
        "不得把维度写成数据表连续堆叠",
        "HTML 读者能先看到结论再看证据",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_explicit_chart_ready_metadata_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "chart_ready",
        "chart_type",
        "x_axis",
        "bar_series",
        "line_series",
        "unit_map",
        "标题 → 图表元信息 → 读图结论 → 纯数值表 → 投资含义",
        "图表元信息不得替代正文判断",
        "纯数值表只允许维度列、年份列和干净数值列",
        "解释、证据、判断、含义、来源、口径说明必须放在表前表后",
        "chart_type 只能使用 line、bar、mixed",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_chart_questions_not_data_dumping():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "每张图回答一个投资问题",
        "图表标题必须是问题型或结论型",
        "图表指标必须在同一因果链上",
        "不得为了凑图表堆数据",
        "ROE 是否穿越周期",
        "现金流是否覆盖资本开支",
        "毛利改善来自价格还是成本",
        "同业对比证明的是成本优势还是只证明规模大",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_investment_question_driven_evidence_tables():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    coordinator = read_text("shared/qualitative/coordinator_v2.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "证据表必须回答一个明确投资问题",
        "投资问题 → 读图结论 → 表格证据 → 投资含义",
        "每组数据必须先说明它在验证哪个判断",
        "表后必须写清楚该组证据如何影响评级、风险或反证阈值",
        "不得只列数据不解释含义",
        "不得把解释性字段混入图表友好数据列",
        "图表友好数据列只放干净数值",
        "读法、解释、证据、影响、判断、含义必须移到表前表后文字或非图表表格",
        "不得把金额和证据写在同一个单元格",
    )
    for text in (prompt, writing_style, coordinator, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_core_operating_profit_recast_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "报表利润 → 核心经营利润 → 可持续利润",
        "核心经营利润重算",
        "剔除非经常性损益、投资收益和一次性因素",
        "可持续利润是否支撑当前评级",
        "计算依据必须能从表格数字复核",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_d3_cycle_roe_repair_chain_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "需求周期 → 价格/成本 → ROE 修复空间 → 反证阈值",
        "只有需求周期、价格/成本和 ROE 修复空间同时改善",
        "评级上修才有基础",
        "D3 数据驱动周期链",
        "3-5 年数据验证需求、价格、成本、毛利率、ROE 和 FCF",
        "同一时间轴上同步改善",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_d2_moat_interrogation_chain_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "护城河六步审讯链",
        "行业地图",
        "量化验证",
        "供给侧优势",
        "需求侧弱点",
        "规模边界",
        "伪优势过滤",
        "竞争对标",
        "可持续 KPI",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_d2_moat_causality_and_disproof_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "不得把高毛利、高 ROE、品牌知名度或市场份额直接当护城河",
        "护城河来源必须拆成可验证机制",
        "供给侧成本优势、需求侧粘性、转换成本、网络效应、渠道控制或客户认证",
        "每个护城河来源必须同时给出反证信号和可持续 KPI",
        "同业对比必须说明差异证明的是结构性优势还是阶段性结果",
        "若优势只来自周期、价格、补贴、汇兑或一次性供需错配，应下调为半真优势或伪优势",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_d4_d5_interrogation_contracts():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "治理红旗排雷清单",
        "审计师变更",
        "资金占用",
        "担保",
        "质押",
        "管理层稳定性",
        "MD&A 审讯表",
        "管理层原始说法",
        "下一年复核指标",
        "风险措辞变化",
        "沉默信息",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_d5_mdna_narrative_audit_disproof_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "D5 不得复述 MD&A 原文后直接给管理层加分",
        "必须把管理层叙事拆成可验证命题",
        "逐项核对收入、毛利率、费用率、现金流、Capex、存货或应收的边际变化",
        "管理层没有解释的边际变化必须列为沉默信息",
        "风险措辞变化必须和实际财务变化交叉验证",
        "若叙事与财务结果不一致，应明确下调管理层叙事可信度",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_next_round_sample_gap_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "至少 4 组图表友好证据模块",
        "图表标题必须是结论型标题",
        "不得用“读图结论：”作为标题前缀",
        "同业坐标表必须包含比较维度",
        "费用端至少拆出两个具体费用项",
        "销售费用 / 管理费用 / 研发费用 / 财务费用",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_validator_exact_generation_contracts():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "D2 的具名同业对比必须放在维度二正文内",
        "同业表第一列必须直接写公司名称",
        "D2 护城河证伪表必须逐字包含支持护城河、削弱护城河、同业/竞品验证、可持续 KPI",
        "D3 数据驱动周期链同一张表必须逐字覆盖需求、价格、成本、毛利率、ROE、FCF",
        "公司类型化证据模块必须同时出现产业坐标、区域/客户结构、同业/区域坐标、单位经济模型、利润桥、现金质量、反证阈值",
        "利润桥重算必须写出计算依据或计算口径",
        "必须出现支撑当前评级或评级仍成立",
        "样板证据模块必须逐字出现收入质量拆分、利润桥、量价成本拆解、现金转化、治理红旗、MD&A 叙事 vs 财务证据、伪优势过滤",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_stable_validator_contract_headings():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "必须使用独立二级标题“## 自适应研究计划”",
        "| 项目 | 判断 | 证据路径 | 反证重点 |",
        "必须使用独立二级标题“## 交叉验证与深度分析”",
        "数字与叙事的匹配、核心矛盾、被忽视信号、非经营项、口径差异",
        "D5 必须同时出现“历史指引”“实际兑现”“新战略”“财务验证”“风险措辞变化”“沉默信息”",
        "必须使用独立二级标题“## 报告局限与数据警示”",
        "必须逐字覆盖：数据口径冲突、同业数据缺口、披露不足、后续复核",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_prompt_requires_cross_validation_reassessment_matrix_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "交叉验证必须输出评级复判表",
        "支持当前评级的证据",
        "削弱当前评级的证据",
        "证据冲突的解释",
        "评级动作：维持 / 下调 / 上调 / 观察",
        "触发重评的最小变量",
        "深度总结必须明确当前评级为什么仍成立或为什么需要调整",
        "不得只重复 D1-D6 小结",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text



def test_qualitative_prompt_requires_industry_evidence_density_and_cross_reassessment():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")

    required_terms = (
        "强周期或重资产公司必须生成公司类型化证据模块",
        "产业坐标",
        "区域/客户结构",
        "同业/区域坐标",
        "单位经济模型必须连接利润桥、现金质量、反证阈值和同业/区域坐标",
        "交叉验证必须输出综合复判",
        "说明当前评级为什么仍成立或为什么需要下调",
    )
    for term in required_terms:
        assert term in prompt
        assert term in writing_style


def test_qualitative_websearch_data_collection_uses_peer_context_and_readable_money_units():
    data_collection = read_text("shared/qualitative/data_collection.md")

    assert "主要竞争对手" in data_collection
    assert "竞品对标" in data_collection
    assert "WebSearch" in data_collection
    assert "金额单位优先使用亿元或万元" in data_collection
    assert "统一转换为 **百万元**" not in data_collection


def test_qualitative_coordinator_requires_websearch_when_peer_context_is_missing():
    coordinator = read_text("shared/qualitative/coordinator_v2.md")

    for term in (
        "§8 行业与竞争",
        "主要竞争对手",
        "待Agent WebSearch补充",
        "先执行 WebSearch 数据补充",
        "data_collection.md",
        "全年",
    ):
        assert term in coordinator


def test_qualitative_peer_evidence_contract_is_independent_and_confidence_tiered():
    data_collection = read_text("shared/qualitative/data_collection.md")
    coordinator = read_text("shared/qualitative/coordinator_v2.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "peer_evidence.md",
        "Peer Evidence / 同业证据包",
        "Confidence",
        "High",
        "Medium",
        "Low",
        "Source type",
        "全年口径",
        "低置信来源不得支撑核心评级",
        "不得硬编码具体样板公司或单一行业同业",
    )
    for text in (data_collection, coordinator, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_peer_evidence_contract_uses_industry_specific_metric_templates():
    data_collection = read_text("shared/qualitative/data_collection.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "强周期/重资产",
        "吨价 / 吨成本 / 吨毛利",
        "制造业/设备",
        "研发率",
        "消费/品牌",
        "渠道结构",
        "软件/互联网/轻资产",
        "客户留存",
        "金融/保险",
        "净息差",
        "行业无法归类",
    )
    for text in (data_collection, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_peer_evidence_contract_keeps_websearch_scope_bounded():
    data_collection = read_text("shared/qualitative/data_collection.md")
    coordinator = read_text("shared/qualitative/coordinator_v2.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "2-4 个",
        "4-6 项",
        "不得扩展成全行业数据库",
        "不追求穷尽同业",
        "WebSearch 能可靠覆盖",
        "找不到统一口径就写 Evidence Gaps",
    )
    for text in (data_collection, coordinator, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_peer_evidence_contract_requires_annual_report_original_wording():
    data_collection = read_text("shared/qualitative/data_collection.md")
    coordinator = read_text("shared/qualitative/coordinator_v2.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "年报原文级",
        "Original wording / 原文摘录",
        "Page clue / 页码线索",
        "Report section / 年报章节",
        "同一指标必须优先使用同一口径",
        "无法取得年报原文级证据",
        "不得用媒体摘要替代 High 证据",
    )
    for text in (data_collection, coordinator, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_d3_external_cycle_evidence_is_lightweight_and_gap_aware():
    data_collection = read_text("shared/qualitative/data_collection.md")
    coordinator = read_text("shared/qualitative/coordinator_v2.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "D3 轻量外部周期证据",
        "2-3 个外部周期变量",
        "年度或全年口径",
        "需求 / 产量",
        "价格趋势",
        "主要成本变量",
        "不新增庞大的周期数据库",
        "找不到就写缺口",
    )
    for text in (data_collection, coordinator, continue_script):
        for term in required_terms:
            assert term in text


def test_qualitative_prompt_requires_d3_external_cycle_evidence_table_contract():
    prompt = read_text("shared/qualitative/qualitative_assessment_v2.md")
    writing_style = read_text("shared/qualitative/agents/writing_style.md")
    continue_script = read_text("shared/qualitative/step5_prompt_template.md")

    required_terms = (
        "D3 外部周期证据表",
        "变量类型 | 年度口径证据 | 来源 | 对财务传导的含义 | 缺口处理",
        "只补 2-3 个变量",
        "需求 / 产量",
        "价格趋势",
        "主要成本变量",
        "不得用零散月度新闻拼接长期序列",
        "不能单独支撑评级上修",
        "找不到年度或全年口径就写缺口",
    )
    for text in (prompt, writing_style, continue_script):
        for term in required_terms:
            assert term in text


def test_turtle_report_template_labels_extreme_threshold_prices_as_diagnostic():
    template = read_text("strategies/turtle/phase3_valuation.md")

    assert "异常低/高的目标买入价" in template
    assert "诊断值" in template
    assert "不得机械表述为基本面目标价" in template


def test_turtle_report_template_requires_financial_sector_adjustments():
    template = read_text("strategies/turtle/phase3_valuation.md")

    assert "金融/银行/保险" in template
    assert "不得机械套用制造业 Capex/D&A" in template
    assert "资本充足率" in template
    assert "拨备" in template


def test_turtle_report_template_requires_negative_aa_gg_diagnostic_handling():
    template = read_text("strategies/turtle/phase3_valuation.md")

    assert "AA/GG" in template
    assert "负值" in template
    assert "诊断值" in template
    assert "不建仓" in template
    assert "高研发" in template
    assert "高资本开支" in template


def test_turtle_report_template_requires_value_trap_filters():
    template = read_text("strategies/turtle/phase3_valuation.md")

    assert "价值陷阱" in template
    assert "低 PE" in template
    assert "低 PB" in template
    assert "应收账款账龄" in template
    assert "坏账" in template
    assert "真实现金回报" in template


def test_turtle_coordinator_uses_canonical_report_filenames():
    coordinator = read_text("strategies/turtle/coordinator.md")
    agent_c_prompt = read_text("strategies/turtle/phase3_valuation.md")
    factor_interface = read_text("strategies/turtle/references/factor_interface.md")

    assert "{code_market}_qualitative_report.md" in coordinator
    assert "{code_market}_turtle_report.md" in coordinator
    assert "{output_dir}/{code_market}_qualitative_report.md" in agent_c_prompt
    assert "{output_dir}/{code_market}_turtle_report.md" in agent_c_prompt
    assert "{output_dir}/{code_market}_qualitative_report.md" in factor_interface

    assert "{output_dir}/qualitative_report.md" not in coordinator
    assert "{output_dir}/qualitative_report.md" not in agent_c_prompt
    assert "{output_dir}/qualitative_report.md" not in factor_interface
    assert "{output_dir}/{company}_{code}_分析报告.md" not in coordinator
    assert "{output_dir}/{公司名}_{代码}_分析报告.md" not in agent_c_prompt


def test_valuation_report_template_requires_finished_report_shell():
    template = read_text("strategies/valuation/references/report_template.md")

    required_sections = [
        "## Valuation Verdict / 估值总体判断",
        "## Valuation Snapshot / 估值快照",
        "## Executive Summary",
        "## 数据来源与免责声明",
    ]

    for section in required_sections:
        assert section in template


def test_valuation_template_requires_financial_sector_method_demotion():
    template = read_text("strategies/valuation/references/report_template.md")

    assert "金融/银行/保险" in template
    assert "DCF/WACC" in template
    assert "降权" in template
    assert "PB/ROE" in template


def test_valuation_template_requires_negative_dcf_demotion_for_heavy_capex_samples():
    template = read_text("strategies/valuation/references/report_template.md")

    assert "负 DCF" in template
    assert "方法适配性诊断" in template
    assert "不得机械主导" in template
    assert "高资本开支" in template


def test_valuation_template_requires_growth_capex_method_convergence():
    template = read_text("strategies/valuation/references/report_template.md")

    assert "高研发" in template
    assert "高资本开支" in template
    assert "PEG" in template
    assert "历史高增长" in template
    assert "安全边际" in template


def test_valuation_template_requires_value_trap_demotion_rules():
    template = read_text("strategies/valuation/references/report_template.md")

    assert "价值陷阱" in template
    assert "高应收" in template
    assert "慢回款" in template
    assert "低 PE" in template
    assert "低 PB" in template
    assert "坏账" in template
    assert "收缩式修复" in template


def test_valuation_coordinator_uses_canonical_report_filenames():
    coordinator = read_text("strategies/valuation/coordinator.md")
    phase2_prompt = read_text("strategies/valuation/phase2_valuation.md")
    template = read_text("strategies/valuation/references/report_template.md")

    assert "{code_market}_qualitative_report.md" in coordinator
    assert "{code_market}_valuation_report.md" in coordinator
    assert "{output_dir}/{code_market}_qualitative_report.md" in phase2_prompt
    assert "{output_dir}/{code_market}_valuation_report.md" in phase2_prompt
    assert "{code_market}_qualitative_report.md" in template

    assert "{output_dir}/qualitative_report.md" not in coordinator
    assert "{output_dir}/qualitative_report.md" not in phase2_prompt
    assert "{output_dir}/{code_market}_{code_market}_qualitative_report.md" not in phase2_prompt
    assert "{output_dir}/{company}_{code}_估值报告.md" not in coordinator
    assert " qualitative_report.md" not in template


def test_readme_active_sections_use_three_canonical_report_outputs():
    readme = read_text("README.md")

    assert "{code_market}_qualitative_report.md" in readme
    assert "{code_market}_turtle_report.md" in readme
    assert "{code_market}_valuation_report.md" in readme
    assert "output/{code}_分析报告.md" not in readme
    assert "report.md + report.html" not in readme


def test_active_prompts_and_scripts_avoid_legacy_qualitative_report_name():
    active_paths = [
        "shared/qualitative/coordinator.md",
        "shared/qualitative/coordinator_v2.md",
        "shared/qualitative/qualitative_assessment.md",
        "shared/qualitative/qualitative_assessment_v2.md",
        "shared/qualitative/agents/agent_summary.md",
        "scripts/report_to_html.py",
        "scripts/valuation_engine.py",
    ]

    legacy_pattern = re.compile(r"(?<![\w}])qualitative_report\.md")
    for path in active_paths:
        text = read_text(path)
        assert legacy_pattern.search(text) is None, path
