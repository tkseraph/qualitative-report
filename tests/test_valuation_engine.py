"""Focused accounting and point-in-time tests for the valuation engine."""

import pandas as pd
import pytest

from tushare_modules.infrastructure import InfrastructureMixin
from valuation_engine import ValuationEngine


class FakeClient:
    def __init__(self, store=None, as_of="20260501"):
        self._store = store or {}
        self.as_of = as_of
        self._currency = "CNY"
        self._fy_end_month = 12

    _safe_float = staticmethod(InfrastructureMixin._safe_float)
    _outflow_amount = staticmethod(InfrastructureMixin._outflow_amount)
    _compact_date = staticmethod(InfrastructureMixin._compact_date)

    def _get_annual_df(self, key):
        df = self._store.get(key)
        if df is None or df.empty:
            return pd.DataFrame()
        return df[df["end_date"].astype(str).str[4:6] == "12"].sort_values(
            "end_date", ascending=False
        )

    def _get_annual_series(self, key, col):
        return [
            (str(row["end_date"])[:4], self._safe_float(row.get(col)))
            for _, row in self._get_annual_df(key).iterrows()
        ]

    def _unit_label(self):
        return "百万元"

    def _price_unit(self):
        return "元"

    def _get_payout_by_year(self):
        return {}


def _engine(store=None, as_of="20260501"):
    return ValuationEngine("600000.SH", "/tmp", FakeClient(store, as_of))


def test_beijing_exchange_uses_a_share_market_parameters():
    assert ValuationEngine("920117.BJ", "/tmp", FakeClient()).market == "A"


def test_cagr_rejects_gapped_series():
    assert ValuationEngine._cagr([100, None, 25]) is None
    assert ValuationEngine._cagr([100, 50, 25]) == pytest.approx(1.0)


@pytest.mark.parametrize("capex", [30.0, -30.0])
def test_fcff_bridge_normalizes_capex_sign(capex):
    store = {
        "income": pd.DataFrame([
            {"end_date": "20241231", "operate_profit": 200, "finance_exp": 20},
        ]),
        "cashflow": pd.DataFrame([
            {
                "end_date": "20241231",
                "c_pay_acq_const_fiolta": capex,
                "depr_fa_coga_dpba": 10,
            },
        ]),
        "balance_sheet": pd.DataFrame([
            {
                "end_date": "20241231", "total_cur_assets": 500,
                "money_cap": 100, "trad_asset": 0, "total_cur_liab": 300,
                "st_borr": 50, "non_cur_liab_due_1y": 0,
            },
            {
                "end_date": "20231231", "total_cur_assets": 450,
                "money_cap": 90, "trad_asset": 0, "total_cur_liab": 280,
                "st_borr": 40, "non_cur_liab_due_1y": 0,
            },
        ]),
    }

    result = _engine(store)._fcff_history({"tax_rate": 25})

    assert result[0]["capex"] == 30
    assert result[0]["fcff"] == pytest.approx(115)


def test_dividends_plus_interest_never_overwrites_dps():
    store = {
        "basic_info": pd.DataFrame([
            {"close": 10, "total_mv": 1000, "total_share": 10},
        ]),
        "dividends": pd.DataFrame([
            {"end_date": "20241231", "cash_div_tax": 1.0},
        ]),
        "cashflow": pd.DataFrame([
            {"end_date": "20241231", "c_pay_dist_dpcp_int_exp": 1_000_000_000},
        ]),
    }

    assert _engine(store)._aggregate_annual_dps() == [("2024", 1.0)]


def _point_in_time_store():
    income = []
    balance = []
    prices = []
    for index, (year, ann_date, shares) in enumerate([
        (2024, "20250401", 100),
        (2023, "20240401", 200),
        (2022, "20230401", 400),
    ]):
        income.append({
            "end_date": f"{year}1231",
            "ann_date": ann_date,
            "f_ann_date": ann_date,
            "basic_eps": 1.0,
            "revenue": 1000.0,
        })
        balance.append({"end_date": f"{year}1231", "total_share": shares})
        prices.extend([
            {"trade_date": str(int(ann_date) - 1), "close": 99.0},
            {"trade_date": str(int(ann_date) + 2), "close": 10.0},
        ])
    return {
        "income": pd.DataFrame(income),
        "balance_sheet": pd.DataFrame(balance),
        "weekly_prices": pd.DataFrame(prices),
        "basic_info": pd.DataFrame([
            {"close": 10, "pe_ttm": 10, "total_mv": 0.04, "total_share": 0.04},
        ]),
    }


def test_pe_band_uses_first_price_after_announcement():
    result = _engine(_point_in_time_store()).pe_band()

    assert result is not None
    assert result["pe_stats"]["median"] == 10
    assert all(obs["price"] == 10 for obs in result["observations"])
    assert all(
        obs["price_date"] >= obs["effective_date"]
        for obs in result["observations"]
    )


def test_ps_uses_historical_reported_share_counts():
    result = _engine(_point_in_time_store()).ps()

    assert result is not None
    observed = {obs["year"]: obs["ps"] for obs in result["observations"]}
    assert observed == {"2024": 1.0, "2023": 2.0, "2022": 4.0}


def test_render_sensitivity_preserves_zero_value():
    rendered = _engine()._render_sensitivity(
        [[0.0, None]],
        [8.0],
        [2.0, 3.0],
        "WACC",
        "g_terminal",
    )

    assert "| 8.00% | 0.00 | N/A |" in rendered


def test_assumptions_find_dcf_by_method_name_not_position():
    method_results = [
        {"method": "PE_Band"},
        None,
        {"method": "DCF", "g_conservative": 4.25},
    ]

    rendered = "\n".join(
        _engine()._render_assumptions_section(
            {"beta": 1.0, "erp": 6.0},
            method_results,
        )
    )

    assert "| 1 | FCF增长率 | 4.25% |" in rendered
