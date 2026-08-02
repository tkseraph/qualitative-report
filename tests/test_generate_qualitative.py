from pathlib import Path
from types import SimpleNamespace

import generate_qualitative
from generate_qualitative import main


def test_generate_qualitative_default_prints_prompt_only_plan_without_nested_claude(tmp_path, capsys):
    output_dir = tmp_path / "output" / "300628_yilian"
    output_dir.mkdir(parents=True)
    (output_dir / "data_pack_market.md").write_text("| 股票代码 | 300628.SZ |\n", encoding="utf-8")
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")

    exit_code = main(["--output-dir", str(output_dir)])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "[generate] stage=step5 qualitative" in captured
    assert "[generate] prompt file:" in captured
    assert "step5_qualitative_prompt.md" in captured
    assert "[generate] target output:" in captured
    assert "300628_SZ_qualitative_report.md" in captured
    assert "[generate] prompt-only mode" in captured
    assert "does not call nested claude -p" in captured
    assert "[generate] validation command:" in captured
    assert "[generate] consistency command:" in captured
    assert "validate_reports.py" in captured
    assert "--type qualitative" in captured
    assert "[generate] next action: run the prompt in the current Claude session, then run validation" in captured
    assert "[generate] model command:" not in captured
    assert "--permission-mode acceptEdits" not in captured


def test_generate_qualitative_requires_existing_inputs(tmp_path, capsys):
    output_dir = tmp_path / "output" / "missing_inputs"
    output_dir.mkdir(parents=True)

    exit_code = main(["--output-dir", str(output_dir)])

    captured = capsys.readouterr().out
    assert exit_code == 2
    assert "Missing required file" in captured
    assert "data_pack_market.md" in captured


def test_generate_qualitative_validation_uses_argv_for_paths_with_spaces(tmp_path, monkeypatch, capsys):
    output_dir = tmp_path / "output with spaces" / "300628 yilian"
    output_dir.mkdir(parents=True)
    (output_dir / "data_pack_market.md").write_text("| 股票代码 | 300628.SZ |\n", encoding="utf-8")
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")
    target_output = output_dir / "300628_SZ_qualitative_report.md"
    calls: list[list[str]] = []

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        if command[0] == "claude":
            target_output.write_text("# qualitative\n", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(generate_qualitative.subprocess, "run", fake_run)

    exit_code = main(["--output-dir", str(output_dir), "--run-nested-claude"])

    assert exit_code == 0
    assert calls[1] == [
        "python",
        str(Path(generate_qualitative.__file__).resolve().parent / "report_consistency.py"),
        "--report",
        str(target_output),
        "--output",
        str(output_dir / "consistency_report.md"),
    ]
    assert calls[2] == [
        "python",
        str(Path(generate_qualitative.__file__).resolve().parent / "validate_reports.py"),
        str(target_output),
        "--type",
        "qualitative",
    ]
    displayed = capsys.readouterr().out
    assert f"'{target_output}'" in displayed


def test_generate_qualitative_precomputes_metrics_in_prompt_only_mode(tmp_path, capsys):
    output_dir = tmp_path / "output" / "300628_yilian"
    output_dir.mkdir(parents=True)
    (output_dir / "data_pack_market.md").write_text(
        """## 1. 基本信息
| 项目 | 内容 |
| --- | ---: |
| 股票代码 | 300628.SZ |
| 当前价格 | 10 |
## 3. 合并利润表
| 项目 | 2024 | 2023 |
| --- | ---: | ---: |
| 营业收入 | 1,000 | 900 |
| 归母净利润 | 100 | 90 |
| 基本EPS | 1 | 0.9 |
""",
        encoding="utf-8",
    )
    (output_dir / "annual_report.pdf").write_bytes(b"%PDF-1.4\n")
    (output_dir / "pdf_sections.json").write_text("{}", encoding="utf-8")

    assert main(["--output-dir", str(output_dir)]) == 0
    computed = output_dir / "computed_metrics.md"
    assert computed.exists()
    assert "CM§1" in computed.read_text(encoding="utf-8")
    assert f"[generate] computed metrics: {computed}" in capsys.readouterr().out
