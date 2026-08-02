"""Tests for advisory cross-passage numeric consistency scanning."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from report_consistency import extract, find_conflicts, main


def test_detects_conflict_and_normalizes_money_units():
    text = "2024 年营业收入 500.00 亿。\n另一段称 2024 年营业收入 56,000 百万元。\n"
    conflicts = find_conflicts(extract(text), 0.05)
    assert [(item["category"], item["year"]) for item in conflicts] == [("营业收入", "2024")]
    assert conflicts[0]["values"] == [500.0, 560.0]


def test_source_tags_are_masked():
    clusters = extract("2024 年营业收入 500 亿元 [src: DP§3 / 999.99 亿元]。")
    values = [observation.value for observations in clusters.values() for observation in observations]
    assert values == [500.0]


def test_nearest_year_and_keyword_avoid_adjacent_contamination():
    text = "2024 年营业利润 122.51 亿元，归母净利润 89.54 亿元；2023 年归母净利润 75.00 亿元。"
    clusters = extract(text)
    assert [item.value for item in clusters[("营业利润", "2024")]] == [122.51]
    assert [item.value for item in clusters[("归母净利润", "2024")]] == [89.54]
    assert [item.value for item in clusters[("归母净利润", "2023")]] == [75.0]


def test_values_within_tolerance_are_clean():
    text = "2024 年毛利率 40.0%。后文重申，2024 年毛利率为 40.5%。"
    assert find_conflicts(extract(text), 0.05) == []


def test_cli_writes_advisory_output(tmp_path):
    report = tmp_path / "qualitative_report.md"
    output = tmp_path / "consistency_report.md"
    report.write_text("2024 年营业收入 500 亿元。\n2024 年营业收入 560 亿元。\n", encoding="utf-8")
    assert main(["--report", str(report), "--output", str(output)]) == 1
    rendered = output.read_text(encoding="utf-8")
    assert "advisory" in rendered
    assert "report_contract/validate_reports" in rendered


@pytest.mark.parametrize("module_mode", [False, True])
def test_direct_and_package_cli_help(module_mode):
    root = Path(__file__).resolve().parent.parent
    command = [sys.executable, "-m", "scripts.report_consistency", "--help"] if module_mode else [
        sys.executable,
        "scripts/report_consistency.py",
        "--help",
    ]
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    assert completed.returncode == 0
    assert "跨段数字一致性" in completed.stdout
