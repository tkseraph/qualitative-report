"""Ensure Phase 3 prompts consume deterministic grids instead of redoing math."""

from pathlib import Path

import pytest


TURTLE_DIR = Path(__file__).resolve().parent.parent / "strategies" / "turtle"


@pytest.fixture(scope="module")
def quantitative_text():
    return (TURTLE_DIR / "phase3_quantitative.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def valuation_text():
    return (TURTLE_DIR / "phase3_valuation.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def interface_text():
    return (TURTLE_DIR / "references" / "factor_interface.md").read_text(encoding="utf-8")


def test_quantitative_agent_does_not_redo_grid_math(quantitative_text):
    assert "你不做数学计算" in quantitative_text
    for section in ("§17.10", "§17.11", "§17.12", "§17.13"):
        assert section in quantitative_text


def test_all_manual_degradation_paths_remain(quantitative_text):
    for section in ("§17.10", "§17.11", "§17.12", "§17.13"):
        assert f"降级路径（{section} 缺失时）" in quantitative_text
    assert "Owner Earnings I = C + D − H" in quantitative_text
    assert "GG = [AA × M × (1−Q%) + O] / 市值" in quantitative_text


def test_quantitative_output_tracks_provenance_and_target(quantitative_text):
    assert "M 来源" in quantitative_text
    assert "GG 来源" in quantitative_text
    assert "目标买入价" in quantitative_text


def test_prompt_anchors_aa_to_reported_equity_fcf(quantitative_text):
    assert "报告口径权益 FCF" in quantitative_text


def test_valuation_uses_precomputed_target(valuation_text):
    assert "§17.11" in valuation_text
    assert "target_buy_price" in valuation_text
    assert "当前股价 × (GG / II)" in valuation_text


@pytest.mark.parametrize("field", ["target_buy_price", "M_source", "GG_source"])
def test_factor_interface_has_grid_provenance_fields(interface_text, field):
    assert field in interface_text
