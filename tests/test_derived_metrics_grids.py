"""Tests for the deterministic §17.10-§17.13 Phase 3 grids."""

import json
import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tushare_collector import TushareClient


MOCK_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "mock_tushare_responses")


def _load_mock(filename: str) -> pd.DataFrame:
    with open(os.path.join(MOCK_DIR, filename), encoding="utf-8") as handle:
        data = json.load(handle)
    return pd.DataFrame(data if isinstance(data, list) else [data])


def _make_client() -> TushareClient:
    with patch("tushare_collector.ts") as mock_ts:
        mock_ts.pro_api.return_value = MagicMock()
        return TushareClient("test_token")


def _base_store(dividend_file: str = "dividend.json") -> dict:
    return {
        "income": _load_mock("income.json").sort_values("end_date", ascending=False),
        "balance_sheet": _load_mock("balancesheet.json").sort_values("end_date", ascending=False),
        "cashflow": _load_mock("cashflow.json").sort_values("end_date", ascending=False),
        "dividends": _load_mock(dividend_file).sort_values("end_date", ascending=False),
        "risk_free_rate": _load_mock("yc_cb.json").sort_values("trade_date", ascending=False),
    }


def _make_grid_client(
    dividend_file: str = "dividend.json",
    *,
    with_basic: bool = True,
) -> TushareClient:
    client = _make_client()
    client._store = _base_store(dividend_file)
    if with_basic:
        client._store["basic_info"] = _load_mock("daily_basic.json")
    client._compute_factor3_step1()
    client._compute_factor3_step4()
    client._compute_factor3_sensitivity_base()
    client._compute_payout_crosscheck()
    return client


class TestPayoutCrosscheck:
    def test_headers_and_methods(self):
        result = _make_grid_client()._compute_payout_crosscheck()
        assert result is not None
        assert "17.10 支付率 M 三重校验" in result
        assert "法1 §6 DPS/EPS" in result
        assert "法2 §5 分配现金/归母" in result
        assert "法3 §17.1 口径" in result

    def test_per_year_values(self):
        result = _make_grid_client()._compute_payout_crosscheck()
        assert "61.01%" in result  # 2024 DPS/EPS
        assert "57.31%" in result  # 2024 distribution cash/profit

    def test_means_preserve_actual_payment_year_method3(self):
        client = _make_grid_client()
        crosscheck = client._store["payout_crosscheck"]
        assert round(crosscheck["m1"], 2) == 58.26
        assert round(crosscheck["m2"], 2) == 54.20
        assert round(crosscheck["m3"], 2) == 52.85
        assert crosscheck["by_year"]["m3"]["2024"] == pytest.approx(54.707, abs=0.001)

    def test_consistent_methods_recommend_local_method3(self):
        client = _make_grid_client()
        crosscheck = client._store["payout_crosscheck"]
        assert crosscheck["m_rec_label"] == "法3"
        assert "M_rec = 52.85%（法3）" in client._compute_payout_crosscheck()

    def test_identical_dps_recommends_cashflow_method(self):
        client = _make_grid_client("dividend_identical.json")
        result = client._compute_payout_crosscheck()
        crosscheck = client._store["payout_crosscheck"]
        assert crosscheck["m_rec_label"] == "法2"
        assert any("填充" in warning for warning in crosscheck["warnings"])
        assert "填充" in result

    def test_large_deviation_recommends_cashflow_method(self):
        client = _make_grid_client()
        client._store["dividends"] = client._store["dividends"].copy()
        client._store["dividends"]["cash_div_tax"] *= 2
        client._compute_payout_crosscheck()
        crosscheck = client._store["payout_crosscheck"]
        assert crosscheck["m_rec_label"] == "法2"
        assert any("> 15%" in warning for warning in crosscheck["warnings"])

    def test_distribution_outflow_sign_is_normalised(self):
        positive = _make_grid_client()
        expected = positive._store["payout_crosscheck"]["m2"]
        negative = _make_grid_client()
        negative._store["cashflow"] = negative._store["cashflow"].copy()
        negative._store["cashflow"]["c_pay_dist_dpcp_int_exp"] *= -1
        negative._compute_payout_crosscheck()
        assert negative._store["payout_crosscheck"]["m2"] == pytest.approx(expected)

    def test_no_income_returns_none(self):
        assert _make_client()._compute_payout_crosscheck() is None


class TestPenetrationGrid:
    def test_headers_and_hurdle(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert result is not None
        assert "17.11 穿透回报率网格" in result
        assert "表A：粗算穿透回报率 R" in result
        assert "表B：精算穿透回报率 GG" in result
        assert "门槛 II = 4.31%" in result

    def test_uses_reported_equity_fcf_aa(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "AA 报告口径权益 FCF" in result
        assert "AA 沿用 §17.5 的报告口径权益 FCF" in result
        assert "2.63%" in result  # AA_2y=8,710m × M_rec / 175,000m

    def test_rough_return_cell(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "3.06%" in result

    def test_target_price_and_hh(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "16.76" in result
        assert "+0.43" in result

    def test_target_price_identity(self):
        client = _make_grid_client()
        payout = client._store["payout_crosscheck"]["m_rec"] / 100
        aa = client._store["factor3_sensitivity"]["aa_2y"]
        market_cap = 17_500_000 * 10_000
        _, hurdle = client._get_rf_ii("600887.SH")
        gg = aa * payout / market_cap * 100
        assert 27.5 * gg / hurdle == pytest.approx(16.76, abs=0.01)

    def test_recommended_method_is_starred(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "法3 52.85% ★" in result
        assert "AA_2y×法3 ★" in result

    def test_buyback_correction_note(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "O = 0（默认）" in result
        assert "0.0571 pct" in result

    def test_taxed_grid_supersedes_tax_free_quick_grid(self):
        result = _make_grid_client()._compute_penetration_grid("600887.SH")
        assert "税前" in result
        assert "以本节 §17.11 为准" in result

    def test_hk_tax_columns_are_deduplicated(self):
        client = _make_grid_client()
        client._currency = "HKD"
        client._store["basic_info"] = pd.DataFrame(
            [{"close": 27.5, "total_market_cap": 175000.0}]
        )
        result = client._compute_penetration_grid("00700.HK")
        assert result is not None
        header = next(line for line in result.splitlines() if line.startswith("| 支付率 M"))
        assert "Q=28%" in header
        assert "Q=20%（默认）" in header
        assert header.count("Q=20%") == 1

    def test_missing_factor3_returns_none(self):
        client = _make_client()
        client._store = {
            "income": _load_mock("income.json"),
            "basic_info": _load_mock("daily_basic.json"),
        }
        assert client._compute_penetration_grid("600887.SH") is None

    def test_missing_market_data_returns_none(self):
        assert _make_grid_client(with_basic=False)._compute_penetration_grid("600887.SH") is None


class TestGGrid:
    def test_header_and_lookup_instruction(self):
        result = _make_grid_client()._compute_g_grid()
        assert result is not None
        assert "17.12 G 系数网格" in result
        assert "LLM 仅选行，禁止自算" in result

    def test_has_twelve_rows(self):
        result = _make_grid_client()._compute_g_grid()
        rows = [line for line in result.splitlines()
                if line.startswith("| 0.") or line.startswith("| 1.")]
        assert len(rows) == 12
        assert rows[0].startswith("| 0.7 |")
        assert rows[-1].startswith("| 1.8 |")

    def test_g_one_owner_earnings_equals_profit(self):
        result = _make_grid_client()._compute_g_grid()
        row = next(line for line in result.splitlines() if line.startswith("| 1.0 |"))
        assert "10,120.00" in row

    def test_g_max_maintenance_capex(self):
        result = _make_grid_client()._compute_g_grid()
        row = next(line for line in result.splitlines() if line.startswith("| 1.8 |"))
        assert "5,760.00" in row

    def test_all_asset_bands(self):
        result = _make_grid_client()._compute_g_grid()
        for band in ("轻", "轻中", "中", "中重", "重"):
            assert band in result

    def test_capex_da_reference_uses_normalised_outflow(self):
        positive = _make_grid_client()._compute_g_grid()
        client = _make_grid_client()
        client._store["cashflow"] = client._store["cashflow"].copy()
        client._store["cashflow"]["c_pay_acq_const_fiolta"] *= -1
        negative = client._compute_g_grid()
        assert "F（Capex/D&A 5年中位数）= 2.48" in positive
        assert "F（Capex/D&A 5年中位数）= 2.48" in negative

    def test_missing_cashflow_returns_none(self):
        client = _make_client()
        client._store = {"income": _load_mock("income.json")}
        assert client._compute_g_grid() is None


class TestRevenueSensitivity:
    def test_lambda_comes_from_reported_fcf_tuple(self):
        client = _make_grid_client()
        factor3 = client._store["factor3_sensitivity"]
        assert factor3["aa_selected"] == pytest.approx(8_710_000_000)
        assert factor3["lambda_median"] == pytest.approx(0.0460829493)
        assert factor3["lambda_reliability"] == "有一项警告"

    def test_header_and_scenario_rows(self):
        result = _make_grid_client()._compute_revenue_sensitivity("600887.SH")
        assert result is not None
        assert "17.13 收入敏感性" in result
        assert "0.0461" in result
        for scenario in ("1.0×", "0.9×", "0.8×", "0.7×"):
            assert scenario in result
        assert "2.63%" in result
        assert "2.46%" in result

    def test_critical_multiple_below_hurdle_is_explicit(self):
        result = _make_grid_client()._compute_revenue_sensitivity("600887.SH")
        assert "临界收入倍数 k* = 2.01" in result
        assert "当前未达门槛" in result

    def test_default_combo_and_reported_fcf_notes(self):
        result = _make_grid_client()._compute_revenue_sensitivity("600887.SH")
        assert "默认组合" in result
        assert "比例缩放" in result
        assert "报告口径权益 FCF" in result

    @pytest.mark.parametrize("coefficient", [None, 0.0])
    def test_missing_or_zero_lambda_degrades(self, coefficient):
        client = _make_grid_client()
        client._store["factor3_sensitivity"]["lambda_median"] = coefficient
        result = client._compute_revenue_sensitivity("600887.SH")
        assert result is not None
        assert "降级" in result
        assert "临界收入倍数 k* = —" in result

    def test_missing_market_data_returns_none(self):
        assert _make_grid_client(with_basic=False)._compute_revenue_sensitivity("600887.SH") is None


class TestPipelineGrids:
    def test_full_pipeline_contains_all_sections(self):
        client = _make_client()
        client._store = _base_store()
        client._store["basic_info"] = _load_mock("daily_basic.json")
        result = client.compute_derived_metrics("600887.SH")
        for section in ("17.10", "17.11", "17.12", "17.13"):
            assert section in result

    def test_empty_store_degrades_gracefully(self):
        result = _make_client().compute_derived_metrics("600887.SH")
        assert "17. 衍生指标" in result
        for section in ("17.10", "17.11", "17.12", "17.13"):
            assert section not in result
