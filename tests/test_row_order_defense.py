"""Price and valuation endpoints must not trust broker response ordering."""

from unittest.mock import MagicMock, patch

import pandas as pd

from tushare_collector import TushareClient


def _client(as_of="2026-03-11"):
    with patch("tushare_collector.ts") as mock_ts:
        mock_ts.pro_api.return_value = MagicMock()
        client = TushareClient("test-token", as_of=as_of)
    client._cache_enabled = False
    return client


def test_a_share_basic_and_market_use_newest_eligible_row():
    client = _client()
    client._cached_basic_call = MagicMock(return_value=pd.DataFrame([{
        "ts_code": "600887.SH", "name": "伊利股份", "fullname": "伊利",
        "industry": "乳品", "area": "内蒙", "exchange": "SSE",
        "list_date": "19960312",
    }]))
    rows = pd.DataFrame([
        {"trade_date": "20250310", "close": 20.0, "high": 21.0, "low": 19.0, "vol": 1,
         "pe_ttm": 10.0, "pb": 2.0, "total_mv": 1, "circ_mv": 1},
        {"trade_date": "20260310", "close": 30.0, "high": 31.0, "low": 29.0, "vol": 2,
         "pe_ttm": 15.0, "pb": 3.0, "total_mv": 2, "circ_mv": 2},
        {"trade_date": "20260312", "close": 99.0, "high": 99.0, "low": 99.0, "vol": 3,
         "pe_ttm": 99.0, "pb": 9.0, "total_mv": 9, "circ_mv": 9},
    ])
    client._safe_call = MagicMock(return_value=rows)

    basic = client.get_basic_info("600887.SH")
    market = client.get_market_data("600887.SH")

    assert "30.0" in basic
    assert "99.0" not in basic
    assert "30.00" in market
    assert str(client._store["basic_info"].iloc[0]["trade_date"]) == "20260310"


def test_hk_valuation_and_market_fallback_use_newest_eligible_row():
    client = _client()
    client._cached_basic_call = MagicMock(return_value=pd.DataFrame([{
        "ts_code": "00700.HK", "name": "腾讯控股", "fullname": "腾讯",
        "market": "主板", "list_date": "20040616", "enname": "Tencent",
    }]))
    valuation = pd.DataFrame([
        {"end_date": "20241231", "pe_ttm": 10.0, "pb_ttm": 2.0, "total_market_cap": 1},
        {"end_date": "20251231", "pe_ttm": 20.0, "pb_ttm": 3.0, "total_market_cap": 2},
        {"end_date": "20261231", "pe_ttm": 99.0, "pb_ttm": 9.0, "total_market_cap": 9},
    ])
    market_rows = pd.DataFrame([
        {"trade_date": "20250310", "close": 300.0, "high": 310.0, "low": 290.0, "vol": 1},
        {"trade_date": "20260310", "close": 400.0, "high": 410.0, "low": 390.0, "vol": 2},
        {"trade_date": "20260312", "close": 999.0, "high": 999.0, "low": 999.0, "vol": 3},
    ])
    client._cached_call = MagicMock(return_value=valuation)
    client._yf_hk_market_data = MagicMock(return_value=None)
    client._safe_call = MagicMock(return_value=market_rows)

    basic = client.get_basic_info("00700.HK")
    market = client.get_market_data("00700.HK")

    assert "20.0" in basic
    assert "99.0" not in basic
    assert "400.00" in market
    assert str(client._store["basic_info"].iloc[0]["end_date"]) == "20251231"


def test_us_valuation_uses_newest_eligible_row():
    client = _client()
    client._cached_basic_call = MagicMock(return_value=pd.DataFrame([{
        "ts_code": "AAPL", "name": "Apple", "enname": "Apple Inc.",
        "market": "NASDAQ", "list_date": "19801212",
    }]))
    client._cached_us_daily = MagicMock(return_value=pd.DataFrame([
        {"trade_date": "20250310", "close": 100.0, "pe": 20.0, "pb": 10.0, "total_mv": 1e9},
        {"trade_date": "20260310", "close": 200.0, "pe": 25.0, "pb": 12.0, "total_mv": 2e9},
        {"trade_date": "20260312", "close": 999.0, "pe": 99.0, "pb": 99.0, "total_mv": 9e9},
    ]))

    result = client.get_basic_info("AAPL.US")

    assert "200.0" in result
    assert "999.0" not in result
    assert str(client._store["basic_info"].iloc[0]["trade_date"]) == "20260310"


def test_balance_sheet_requests_and_renders_new_liability_fields():
    client = _client()
    frame = pd.DataFrame([{
        "end_date": "20251231", "ann_date": "20260201", "report_type": "1",
        "payroll_payable": 1, "taxes_payable": 2, "oth_payable": 3,
        "lt_payable": 4, "lease_liab": 5, "provisions": 6,
        "defer_inc_non_cur_liab": 7,
    }])
    client._cached_call = MagicMock(return_value=frame)

    result = client.get_balance_sheet("600887.SH")

    requested = client._cached_call.call_args.kwargs["fields"]
    for field in (
        "payroll_payable", "taxes_payable", "oth_payable", "lt_payable",
        "lease_liab", "provisions", "defer_inc_non_cur_liab",
    ):
        assert field in requested
    for label in (
        "应付职工薪酬", "应交税费", "其他应付款", "长期应付款",
        "租赁负债", "预计负债", "递延收益",
    ):
        assert label in result
