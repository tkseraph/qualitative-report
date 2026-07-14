"""Smoke tests for supported package imports and module-mode CLI entry points."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "module_name",
    (
        "scripts.tushare_collector",
        "scripts.valuation_engine",
        "scripts.screener_core",
        "scripts.report_to_html",
        "scripts.wechat_report",
        "scripts.generate_qualitative",
    ),
)
def test_production_module_can_be_imported_as_package(module_name: str):
    assert importlib.import_module(module_name) is not None


@pytest.mark.parametrize(
    "module_name",
    ("scripts.valuation_engine", "scripts.screener_core"),
)
def test_cli_help_works_in_module_mode(module_name: str):
    result = subprocess.run(
        [sys.executable, "-m", module_name, "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
