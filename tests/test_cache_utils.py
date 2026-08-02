"""Tests for the shared Parquet-backed DataFrame cache."""

import time
from unittest.mock import patch

import pandas as pd

from cache_utils import ScreenerCache


def test_cache_round_trip(tmp_path):
    cache = ScreenerCache(str(tmp_path / "cache"))
    expected = pd.DataFrame({"number": [1, 2], "name": ["a", "b"]})

    cache.put("key", expected)

    actual = cache.get("key", ttl_seconds=3600)
    assert actual is not None
    assert actual.equals(expected)


def test_expired_entry_is_a_miss(tmp_path):
    cache = ScreenerCache(str(tmp_path / "cache"))
    cache.put("key", pd.DataFrame({"number": [1]}))

    with patch("cache_utils.time.time", return_value=time.time() + 3601):
        assert cache.get("key", ttl_seconds=3600) is None


def test_invalidate_prefix_only_removes_matching_keys(tmp_path):
    cache = ScreenerCache(str(tmp_path / "cache"))
    frame = pd.DataFrame({"number": [1]})
    cache.put("collector_600887.SH_20260311_income", frame)
    cache.put("collector_600887.SH_20260312_income", frame)
    cache.put("collector_000858.SZ_20260311_income", frame)

    cache.invalidate_prefix("collector_600887.SH_")

    assert cache.get("collector_600887.SH_20260311_income", 3600) is None
    assert cache.get("collector_600887.SH_20260312_income", 3600) is None
    assert cache.get("collector_000858.SZ_20260311_income", 3600) is not None


def test_invalidate_and_clear(tmp_path):
    cache = ScreenerCache(str(tmp_path / "cache"))
    frame = pd.DataFrame({"number": [1]})
    cache.put("one", frame)
    cache.put("two", frame)

    cache.invalidate("one")
    assert cache.get("one", 3600) is None
    assert cache.get("two", 3600) is not None

    cache.clear()
    assert cache.get("two", 3600) is None
