"""Regression tests for the collector TTL cache and rate controls."""

from unittest.mock import MagicMock, patch

import pandas as pd

from tushare_collector import TushareClient, rate_limit


def _client(tmp_path, as_of="2026-03-11"):
    with patch("tushare_collector.ts") as mock_ts:
        mock_ts.pro_api.return_value = MagicMock()
        client = TushareClient("test-token", as_of=as_of)
    client._cache_dir = str(tmp_path / "collector")
    return client


class TestConfigurableRateDelay:
    def test_zero_skips_sleep(self, monkeypatch):
        monkeypatch.setenv("TUSHARE_RATE_DELAY", "0")

        @rate_limit
        def call():
            return "ok"

        with patch("tushare_collector.time.sleep") as sleep:
            assert call() == "ok"
        sleep.assert_not_called()

    def test_custom_and_invalid_values(self, monkeypatch):
        @rate_limit
        def call():
            return None

        monkeypatch.setenv("TUSHARE_RATE_DELAY", "0.1")
        with patch("tushare_collector.time.sleep") as sleep:
            call()
        sleep.assert_called_once_with(0.1)

        monkeypatch.setenv("TUSHARE_RATE_DELAY", "invalid")
        with patch("tushare_collector.time.sleep") as sleep:
            call()
        sleep.assert_called_once_with(0.5)


class TestCollectorTtlCache:
    @staticmethod
    def _income():
        return pd.DataFrame([
            {"ts_code": "600887.SH", "end_date": "20251231", "revenue": 1}
        ])

    def test_identical_call_hits_cache(self, tmp_path):
        client = _client(tmp_path)
        client._safe_call = MagicMock(return_value=self._income())

        first = client._cached_call("income", ts_code="600887.SH", report_type="1")
        second = client._cached_call("income", ts_code="600887.SH", report_type="1")

        assert client._safe_call.call_count == 1
        assert first.equals(second)

    def test_as_of_is_part_of_cache_identity(self, tmp_path):
        client = _client(tmp_path)
        client._safe_call = MagicMock(return_value=self._income())

        key = client._ttl_cache_key("income", {"ts_code": "600887.SH"})
        assert "_20260311_" in key
        client._cached_call("income", ts_code="600887.SH")

        client.as_of = "20260312"
        client._cached_call("income", ts_code="600887.SH")
        assert client._safe_call.call_count == 2

    def test_kwargs_and_stock_codes_have_distinct_entries(self, tmp_path):
        client = _client(tmp_path)
        client._safe_call = MagicMock(return_value=self._income())

        client._cached_call("income", ts_code="600887.SH", report_type="1")
        client._cached_call("income", ts_code="600887.SH", report_type="6")
        client._cached_call("income", ts_code="000858.SZ", report_type="1")

        assert client._safe_call.call_count == 3

    def test_disabled_non_cacheable_and_empty_results_bypass_cache(self, tmp_path):
        client = _client(tmp_path)
        client._safe_call = MagicMock(return_value=self._income())
        client._cache_enabled = False
        client._cached_call("income", ts_code="600887.SH")
        client._cached_call("income", ts_code="600887.SH")
        assert client._safe_call.call_count == 2

        client._cache_enabled = True
        client._cached_call("daily", ts_code="600887.SH")
        client._cached_call("daily", ts_code="600887.SH")
        assert client._safe_call.call_count == 4

        client._safe_call = MagicMock(return_value=pd.DataFrame())
        client._cached_call("cashflow", ts_code="600887.SH")
        client._cached_call("cashflow", ts_code="600887.SH")
        assert client._safe_call.call_count == 2

    def test_refresh_prefix_clears_every_as_of_for_one_stock(self, tmp_path):
        client = _client(tmp_path)
        client._safe_call = MagicMock(return_value=self._income())
        client._cached_call("income", ts_code="600887.SH")
        client.as_of = "20260312"
        client._cached_call("income", ts_code="600887.SH")
        assert client._safe_call.call_count == 2

        client._get_ttl_cache().invalidate_prefix("collector_600887.SH_")
        client._cached_call("income", ts_code="600887.SH")
        assert client._safe_call.call_count == 3


def test_screener_honors_configurable_rate_delay(monkeypatch):
    from screener_core import TushareScreener

    screener = object.__new__(TushareScreener)
    screener._pro = MagicMock()
    screener._pro.income.return_value = pd.DataFrame()
    screener._get_pro = MagicMock(return_value=screener._pro)
    monkeypatch.setenv("TUSHARE_RATE_DELAY", "0")

    with patch("screener_core.time.sleep") as sleep:
        screener._safe_call("income")
    sleep.assert_not_called()
