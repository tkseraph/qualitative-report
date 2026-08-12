from pathlib import Path
import shlex
import sys

import pytest

from continue_single_stock import (
    _consistency_argv,
    _consistency_command,
    _validation_argv,
    _validation_command,
    build_step5_prompt,
    build_step7_prompt,
    build_step8_prompt,
    detect_code_prefix,
    main,
)


PROJECT_ROOT = Path("/repo")
OUTPUT_DIR = Path("/repo/output/600018_test")
QUALITATIVE = OUTPUT_DIR / "600018_SH_qualitative_report.md"
TURTLE = OUTPUT_DIR / "600018_SH_turtle_report.md"
VALUATION = OUTPUT_DIR / "600018_SH_valuation_report.md"


def test_detect_code_prefix_accepts_beijing_exchange(tmp_path):
    (tmp_path / "data_pack_market.md").write_text(
        "| 股票代码 | 920117.BJ |\n", encoding="utf-8"
    )
    assert detect_code_prefix(tmp_path) == "920117_BJ"


def test_step5_prompt_requires_qualitative_shell_and_validation():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert str(QUALITATIVE) in prompt
    assert "Business Quality Verdict / 商业质量总体评级" in prompt
    assert "Quality Snapshot / 质量快照" in prompt
    assert "数据来源与免责声明" in prompt
    assert f"{sys.executable} {PROJECT_ROOT / 'scripts' / 'validate_reports.py'}" in prompt
    assert "--type qualitative" in prompt


def test_step5_prompt_wires_budget_provenance_and_advisory_audit():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        str(OUTPUT_DIR / "computed_metrics.md"),
        "CM§1-CM§6",
        "不得出现 `[src: ...]`",
        "qualitative_evidence.json",
        "lead-with-numbers",
        "只能作历史经验参考",
        "cleanroom_audit.md",
        "numeric_audit.md",
        str(OUTPUT_DIR / "consistency_report.md"),
        "退出码 1 表示发现提示性冲突",
        "report_contract.json",
        "validate_reports.py",
    ):
        assert term in prompt


def test_step5_prompt_requires_sample_quality_first_screen_and_refutation():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "核心矛盾与反证条件" in prompt
    assert "最大风险" in prompt
    assert "反证条件" in prompt
    assert "预警阈值" in prompt
    assert "触发后的重评动作" in prompt


def test_step5_prompt_requires_wechat_readability_constraints():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "微信公众号" in prompt
    assert "段落不要过长" in prompt
    assert "表格" in prompt
    assert "每张表" in prompt
    assert "结论句" in prompt


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


def test_step5_prompt_requires_fixed_first_screen_card_schema_and_machine_fields():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "| 项目 | 结论 |" in prompt
    assert "不要使用“问题 / 回答”或“判断项 / 结论 / 核心依据”替代表头" in prompt
    for field in (
        "analysis_contract_version",
        "roe_history_years",
        "roe_available_years_avg",
        "sotp_economic_separability",
        "roe_5y_avg",
        "moat_rating",
        "moat_sustainability",
        "management_rating",
        "cyclicality",
        "cycle_position",
        "capital_intensity",
        "entry_barrier",
        "moat_existence",
    ):
        assert field in prompt


def test_step5_prompt_requires_validator_quality_gate_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "五个核心发现" in prompt
    assert "D1-D6 每个维度" in prompt
    assert "本章结论、最重要证据、观察风险 / 重评触发" in prompt
    assert "数据来源和免责声明之后" in prompt
    assert "validate_reports.py" in prompt


def test_step5_prompt_requires_sample_evidence_modules():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "收入质量拆分",
        "利润桥",
        "量价成本拆解",
        "现金转化",
        "治理红旗",
        "MD&A 叙事 vs 财务证据",
        "伪优势过滤",
    ):
        assert term in prompt


def test_step5_prompt_requires_appendix_and_framework_deemphasis_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "附录和框架说明降权",
        "报告局限、数据警示、结构化参数、分析框架与评级标准只能作为附录材料",
        "不得在 Executive Summary、D1-D6 或深度总结中解释框架定义",
        "不得把 Greenwald、护城河框架、评级标准写成主线段落",
        "正文只写公司判断、证据和投资含义",
        "附录内容不得压过 Business Quality Verdict、Executive Summary、D1-D6、交叉验证、深度总结和未来观察变量",
        "结构化参数只用于机器读取和 HTML 折叠面板",
        "分析框架说明只用于读者需要时展开阅读",
    ):
        assert term in prompt



def test_step5_prompt_requires_dimension_narrative_rhythm_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "维度正文节奏",
        "判断句 → 证据模块 → 投资含义 → 本章小结",
        "每个维度第一段必须先给出本章判断",
        "证据模块不得连续堆叠超过两张表",
        "每个核心表格后必须回扣核心商业质量问题",
        "本章小结必须压缩为本章结论、最重要证据、观察风险 / 重评触发",
        "不得把维度写成数据表连续堆叠",
        "HTML 读者能先看到结论再看证据",
    ):
        assert term in prompt



def test_step5_prompt_requires_explicit_chart_ready_metadata_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_requires_generation_first_wechat_quality():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "源报告",
        "不得依赖微信后处理",
        "公司类型化证据模块",
        "每个维度至少一组公司专属证据",
        "公司专属数字",
        "轻资产公司",
        "强周期公司",
        "单位经济模型",
        "Capex/D&A",
    ):
        assert term in prompt


def test_step5_prompt_requires_dimension_argument_chains_for_wechat_style():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_forbids_instruction_like_table_prose_in_body():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert "不得把结构说明照抄成正文" in prompt
    assert "这张表回答" in prompt
    assert "读者化结论句" in prompt


def test_step5_prompt_treats_sample_chains_as_internal_checklist_not_body_text():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "内部写作检查清单",
        "不得把结构词",
        "表格任务说明",
        "模型指令",
        "表前",
        "表后",
        "投资含义",
    ):
        assert term in prompt


def test_step5_prompt_requires_d4_d5_d6_depth_contracts():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "D4 必须同时覆盖治理红旗、管理层/控制权、资本配置、承诺兑现",
        "D5 必须同时覆盖历史指引、实际兑现、新战略、财务验证、风险措辞变化、沉默信息、重评动作",
        "D6 必须同时覆盖触发条件、子公司、投资收益、SOTP 判断、阈值和计算依据",
    ):
        assert term in prompt


def test_step5_prompt_requires_per_dimension_company_specific_evidence_and_thresholds():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "每个维度至少一组公司专属证据",
        "不得只写通用框架语",
        "D3 必须输出周期/外部变量敏感性表",
        "当前阶段 → 外部变量 → 财务敏感性 → 预警阈值 → 重评动作",
        "触发测试、数据完备度、决策原因",
        "共享资源或关联持股的重复计价检查",
    ):
        assert term in prompt


def test_step5_prompt_requires_p0_p2_sample_gap_closures():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "公司赚钱公式",
        "收入来源 → 利润驱动 → 资本占用 → 现金转化 → 关键反证",
        "护城河证伪表",
        "支持护城河的证据",
        "削弱护城河的反证",
        "管理层叙事审计表",
        "管理层说法 → 财务验证 → 是否兑现 → 沉默信息 → 重评动作",
    ):
        assert term in prompt


def test_step5_prompt_requires_d2_moat_causality_and_disproof_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "不得把高毛利、高 ROE、品牌知名度或市场份额直接当护城河",
        "护城河来源必须拆成可验证机制",
        "供给侧成本优势、需求侧粘性、转换成本、网络效应、渠道控制或客户认证",
        "每个护城河来源必须同时给出反证信号和可持续 KPI",
        "同业对比必须说明差异证明的是结构性优势还是阶段性结果",
        "若优势只来自周期、价格、补贴、汇兑或一次性供需错配，应下调为半真优势或伪优势",
    ):
        assert term in prompt



def test_step5_prompt_requires_review_tables_limitations_and_public_cleanliness():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "资本配置复盘表",
        "动作 → 金额 → 管理层理由 → 后续结果 → 质量评价",
        "历史目标 vs 实际兑现表",
        "年份 → 管理层目标 → 实际结果 → 偏差 → 投资含义",
        "报告局限与数据警示",
        "数据口径冲突、同业数据缺口、披露不足事项及后续复核动作",
        "不得出现本地绝对路径",
        "不得出现 WebSearch fallback",
        "acceptance samples",
    ):
        assert term in prompt


def test_step5_prompt_requires_industry_evidence_density_and_cross_reassessment():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "强周期或重资产公司必须生成公司类型化证据模块",
        "产业坐标",
        "区域/客户结构",
        "同业/区域坐标",
        "单位经济模型必须连接利润桥、现金质量、反证阈值和同业/区域坐标",
        "交叉验证必须输出综合复判",
        "说明当前评级为什么仍成立或为什么需要下调",
    ):
        assert term in prompt


def test_step5_prompt_requires_cross_validation_reassessment_matrix_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "交叉验证必须输出评级复判表",
        "支持当前评级的证据",
        "削弱当前评级的证据",
        "证据冲突的解释",
        "评级动作：维持 / 下调 / 上调 / 观察",
        "触发重评的最小变量",
        "深度总结必须明确当前评级为什么仍成立或为什么需要调整",
        "不得只重复 D1-D6 小结",
    ):
        assert term in prompt



def test_step5_prompt_requires_unit_economics_and_observation_priority_tiers():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_requires_d5_mdna_narrative_audit_disproof_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "D5 不得复述 MD&A 原文后直接给管理层加分",
        "必须把管理层叙事拆成可验证命题",
        "逐项核对收入、毛利率、费用率、现金流、Capex、存货或应收的边际变化",
        "管理层没有解释的边际变化必须列为沉默信息",
        "风险措辞变化必须和实际财务变化交叉验证",
        "若叙事与财务结果不一致，应明确下调管理层叙事可信度",
    ):
        assert term in prompt



def test_step5_prompt_requires_multi_year_trend_and_d4_d5_delivery_status():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "近五年质量趋势",
        "ROE / 毛利率 / 净利率 / FCF / Capex/D&A",
        "趋势证据",
        "多年复盘状态",
        "多年兑现状态",
        "不能只写当年事实",
    ):
        assert term in prompt


def test_step5_prompt_requires_stable_validator_contract_headings():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "必须使用独立二级标题“## 自适应研究计划”",
        "| 项目 | 判断 | 证据路径 | 反证重点 |",
        "必须使用独立二级标题“## 交叉验证与深度分析”",
        "数字与叙事的匹配、核心矛盾、被忽视信号、非经营项、口径差异",
        "D5 必须同时出现“历史指引”“实际兑现”“新战略”“财务验证”“风险措辞变化”“沉默信息”",
        "必须使用独立二级标题“## 报告局限与数据警示”",
        "必须逐字覆盖：数据口径冲突、同业数据缺口、披露不足、后续复核",
    ):
        assert term in prompt


def test_step5_prompt_requires_html_renderer_contract_for_finished_quality():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_requires_sample_level_chart_ready_archetypes():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "至少 5 个可渲染图表",
        "五类图表原型",
        "业务或区域结构",
        "资本消耗",
        "Capex/D&A 或资本开支 vs 折旧摊销",
        "现金转化",
        "OCF/净利润、营运资本或应收账款",
        "盈利能力趋势",
        "ROE / 毛利率 / 净利率",
        "同业或效率对比",
        "现金转化图必须显式 chart_ready",
        "chart_ready 元信息或图表正文必须显式出现 OCF/净利润、营运资本或应收账款",
    ):
        assert term in prompt


def test_step5_prompt_requires_d3_summary_and_d6_trigger_heading_contract():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "D3 的本章小结必须保留在维度三章节内部",
        "不得把近五年质量趋势作为独立二级标题插入 D3 和本章小结之间",
        "D6 必须使用小标题“### SOTP 触发决策表”",
    ):
        assert term in prompt


def test_step5_prompt_requires_asset_light_tech_hardware_branch():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_requires_single_core_quality_question_thread():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
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
    ):
        assert term in prompt


def test_step5_prompt_requires_websearch_peer_context_prefill_when_missing():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    for term in (
        "§8 行业与竞争",
        "主要竞争对手",
        "待Agent WebSearch补充",
        "先执行 WebSearch 数据补充",
        "data_collection.md",
        "全年",
    ):
        assert term in prompt


def test_prompt_validation_commands_use_absolute_validate_script():
    prompt = build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)

    assert f"{sys.executable} {PROJECT_ROOT / 'scripts' / 'validate_reports.py'} {QUALITATIVE} --type qualitative --quality-contract current" in prompt
    assert "python scripts/validate_reports.py" not in prompt


def test_validation_command_preserves_paths_with_spaces():
    project_root = Path("/repo with spaces")
    report = Path("/output with spaces/qualitative report.md")

    argv = _validation_argv(project_root, report, "qualitative")

    assert argv == [
        sys.executable,
        "/repo with spaces/scripts/validate_reports.py",
        "/output with spaces/qualitative report.md",
        "--type",
        "qualitative",
        "--quality-contract",
        "current",
    ]
    assert shlex.split(_validation_command(project_root, report, "qualitative")) == argv


def test_consistency_command_preserves_paths_with_spaces():
    project_root = Path("/repo with spaces")
    report = Path("/tmp/output with spaces/report.md")
    output = Path("/tmp/output with spaces/consistency.md")

    argv = _consistency_argv(project_root, report, output)

    assert shlex.split(_consistency_command(project_root, report, output)) == argv


def test_step5_prompt_body_is_loaded_from_external_template():
    root = Path(__file__).resolve().parents[1]
    template = (root / "shared" / "qualitative" / "step5_prompt_template.md").read_text(encoding="utf-8")
    implementation = (root / "scripts" / "continue_single_stock.py").read_text(encoding="utf-8")

    assert "${report_name}" in template
    assert "${validation_command}" in template
    assert "必须保留并强化成品报告外壳" in template
    assert "必须保留并强化成品报告外壳" not in implementation
    assert "${" not in build_step5_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE)


def test_step7_prompt_generates_turtle_report_and_validation():
    prompt = build_step7_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE, TURTLE)

    assert str(QUALITATIVE) in prompt
    assert str(TURTLE) in prompt
    assert "strategies/turtle/coordinator.md" in prompt
    assert "strategies/turtle/phase3_valuation.md" in prompt
    assert "Strategy Verdict" in prompt
    assert "Turtle Snapshot / 核心指标快照" in prompt
    assert f"{sys.executable} {PROJECT_ROOT / 'scripts' / 'validate_reports.py'}" in prompt
    assert "--type turtle" in prompt


def test_step8_prompt_generates_valuation_report_and_validation():
    prompt = build_step8_prompt(PROJECT_ROOT, OUTPUT_DIR, QUALITATIVE, VALUATION)

    assert str(QUALITATIVE) in prompt
    assert str(VALUATION) in prompt
    assert "strategies/valuation/coordinator.md" in prompt
    assert "strategies/valuation/phase2_valuation.md" in prompt
    assert "Valuation Verdict / 估值总体判断" in prompt
    assert "Valuation Snapshot / 估值快照" in prompt
    assert f"{sys.executable} {PROJECT_ROOT / 'scripts' / 'validate_reports.py'}" in prompt
    assert "--type valuation" in prompt


def test_run_single_stock_script_mentions_three_prompt_files_and_directory_validation():
    script = (Path(__file__).resolve().parents[1] / "scripts" / "run_single_stock.py").read_text(encoding="utf-8")

    assert "step5_qualitative_prompt.md" in script
    assert "step7_turtle_prompt.md" in script
    assert "step8_valuation_prompt.md" in script
    assert "prepare_computed_metrics(output_dir)" in script
    assert "_validation_command(project_root, output_dir)" in script


def test_readme_documents_single_stock_three_report_flow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "run_single_stock.py" in readme
    assert "continue_single_stock.py" in readme
    assert "--stage step5" in readme
    assert "--stage step7" in readme
    assert "--stage step8" in readme
    assert "step5_qualitative_prompt.md" in readme
    assert "step7_turtle_prompt.md" in readme
    assert "step8_valuation_prompt.md" in readme
    assert "validate_reports.py" in readme
    assert "quality_control.py" in readme
    assert "report_consistency.py" in readme
    assert "computed_metrics.md" in readme
    assert "--type qualitative" in readme
    assert "--type turtle" in readme
    assert "--type valuation" in readme


def test_readme_documents_step7_quantitative_prerequisite_behavior():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "phase3_quantitative.md" in readme
    assert "若不存在，请按 turtle coordinator 先生成" in readme
    assert "Step 7 不要求 phase3_quantitative.md 预先存在" in readme


def test_readme_documents_fresh_e2e_acceptance_flow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "最终交付前建议选一个未手工修过的新 A 股样例" in readme
    assert "runner → Step 5 → Step 7 → Step 8 → 目录验收" in readme
    assert "不要只复用已人工补齐的 acceptance 样例" in readme


def test_readme_documents_fixed_acceptance_matrix():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "固定验收矩阵" in readme
    assert "金融 / 银行" in readme
    assert "强周期 / 重资产" in readme
    assert "高研发 / 高资本开支成长制造" in readme
    assert "质量下滑 / 价值陷阱" in readme
    assert "优质但估值不便宜" in readme
    assert "688668_dingtong_e2e_fresh" in readme


def _write_market_pack(output_dir: Path) -> None:
    (output_dir / "data_pack_market.md").write_text("| 股票代码 | 600018.SH |\n", encoding="utf-8")


def _run_continue(output_dir: Path, stage: str) -> None:
    old_argv = sys.argv
    try:
        sys.argv = ["continue_single_stock.py", "--output-dir", str(output_dir), "--stage", stage]
        main()
    finally:
        sys.argv = old_argv


def test_continue_cli_stage5_writes_qualitative_prompt(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")

    _run_continue(output_dir, "step5")

    prompt_path = output_dir / "step5_qualitative_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_qualitative_report.md" in prompt
    assert "--type qualitative" in prompt


def test_continue_cli_stage7_writes_turtle_prompt_without_quantitative_file(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")

    _run_continue(output_dir, "step7")

    prompt_path = output_dir / "step7_turtle_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_turtle_report.md" in prompt
    assert "phase3_quantitative.md" in prompt
    assert "若不存在，请按 turtle coordinator 先生成" in prompt
    assert "--type turtle" in prompt


def test_continue_cli_stage8_writes_valuation_prompt(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")
    (output_dir / "valuation_computed.md").write_text("# computed", encoding="utf-8")

    _run_continue(output_dir, "step8")

    prompt_path = output_dir / "step8_valuation_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_valuation_report.md" in prompt
    assert "Valuation Verdict / 估值总体判断" in prompt
    assert "--type valuation" in prompt


def test_continue_detects_code_prefix_from_existing_report_when_market_pack_lacks_code(tmp_path):
    output_dir = tmp_path / "resume_case"
    output_dir.mkdir()
    (output_dir / "data_pack_market.md").write_text("# 数据包\n无股票代码字段\n", encoding="utf-8")
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")
    (output_dir / "valuation_computed.md").write_text("# computed", encoding="utf-8")

    _run_continue(output_dir, "step8")

    prompt_path = output_dir / "step8_valuation_prompt.md"
    prompt = prompt_path.read_text(encoding="utf-8")
    assert prompt_path.exists()
    assert "600018_SH_valuation_report.md" in prompt


def test_continue_cli_stage8_fails_when_valuation_computed_missing(tmp_path):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "600018_SH_qualitative_report.md").write_text("# qualitative", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        _run_continue(output_dir, "step8")

    assert "Missing required file" in str(exc.value)
    assert "valuation_computed.md" in str(exc.value)


def test_continue_cli_stage_all_writes_three_prompts_and_final_validation(tmp_path, capsys):
    output_dir = tmp_path / "600018_sipg"
    output_dir.mkdir()
    _write_market_pack(output_dir)
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")
    (output_dir / "valuation_computed.md").write_text("# computed", encoding="utf-8")

    _run_continue(output_dir, "all")

    step5_prompt_path = output_dir / "step5_qualitative_prompt.md"
    step7_prompt_path = output_dir / "step7_turtle_prompt.md"
    step8_prompt_path = output_dir / "step8_valuation_prompt.md"
    assert step5_prompt_path.exists()
    assert step7_prompt_path.exists()
    assert step8_prompt_path.exists()

    validate_script = Path(__file__).resolve().parents[1] / "scripts" / "validate_reports.py"
    step5_prompt = step5_prompt_path.read_text(encoding="utf-8")
    step7_prompt = step7_prompt_path.read_text(encoding="utf-8")
    step8_prompt = step8_prompt_path.read_text(encoding="utf-8")
    for term in (
        "至少 5 个可渲染图表",
        "五类图表原型",
        "业务或区域结构",
        "资本消耗",
        "Capex/D&A 或资本开支 vs 折旧摊销",
        "现金转化",
        "OCF/净利润、营运资本或应收账款",
        "盈利能力趋势",
        "ROE / 毛利率 / 净利率",
        "同业或效率对比",
    ):
        assert term in step5_prompt
    assert f"python {validate_script} {output_dir.resolve() / '600018_SH_qualitative_report.md'} --type qualitative" in step5_prompt
    assert f"python {validate_script} {output_dir.resolve() / '600018_SH_turtle_report.md'} --type turtle" in step7_prompt
    assert f"python {validate_script} {output_dir.resolve() / '600018_SH_valuation_report.md'} --type valuation" in step8_prompt

    captured = capsys.readouterr()
    assert "Final three-report validation" in captured.out
    assert f"python {validate_script} {output_dir.resolve()}" in captured.out


def test_readme_documents_low_friction_local_workflow():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "本地低摩擦工作流" in readme
    assert "run_single_stock.py" in readme
    assert "continue_single_stock.py" in readme
    assert "--stage all" in readme
    assert "人工生成三报告" in readme
    assert "目录验收" in readme


def test_readme_documents_continue_stage_all():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "step5" in readme
    assert "step7" in readme
    assert "step8" in readme
    assert "all" in readme
    assert "支持四个 stage" in readme


def test_readme_documents_current_pdf_section_mapping():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")

    assert "| P2 | 受限资产" in readme
    assert "| P3 | 应收账款账龄" in readme
    assert "| P4 | 关联方交易" in readme
    assert "| P6 | 或有负债" in readme
    assert "| P13 | 非经常性损益" in readme
