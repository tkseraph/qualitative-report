#!/usr/bin/env python3
"""Turtle Investment Framework - Tushare Data Collector (Phase 1A).

Facade module: re-exports all public names and defines TushareClient
which inherits from mixin classes in tushare_modules/.

Collects 5 years of financial data from Tushare Pro API and outputs
a structured data_pack_market.md file.

Usage:
    python3 scripts/tushare_collector.py --code 600887.SH
    python3 scripts/tushare_collector.py --code 600887.SH --output output/data_pack.md
    python3 scripts/tushare_collector.py --code 600887.SH --dry-run
"""

import argparse
import functools
import os
import sys
import time
from pathlib import Path

import pandas as pd
import tushare as ts

try:
    import yfinance as yf
    _yf_available = True
except ImportError:
    class _MissingYFinance:
        @staticmethod
        def Ticker(*_args, **_kwargs):
            raise RuntimeError("yfinance is not installed")

    yf = _MissingYFinance()
    _yf_available = False

if __package__:
    from .config import get_token, get_api_url, validate_stock_code
    from .data_snapshot import load_snapshot, save_snapshot, snapshot_exists
    from .format_utils import format_number, format_table, format_header
else:
    from config import get_token, get_api_url, validate_stock_code
    from data_snapshot import load_snapshot, save_snapshot, snapshot_exists
    from format_utils import format_number, format_table, format_header

# Re-export all constants and mixin classes for backward compatibility.
# Tests and external code import these from tushare_collector directly:
#   from tushare_collector import TushareClient, WarningsCollector, rate_limit
#   from tushare_collector import _VIP_MAP, HK_INCOME_MAP, US_INCOME_MAP
if __package__:
    from .tushare_modules import (
        _VIP_MAP,
        HK_INCOME_MAP, HK_BALANCE_MAP, HK_CASHFLOW_MAP,
        US_INCOME_MAP, US_BALANCE_MAP, US_CASHFLOW_MAP,
        _YF_INCOME_MAP, _YF_BALANCE_MAP, _YF_CASHFLOW_MAP,
        InfrastructureMixin, YFinanceMixin, FinancialsMixin,
        OtherDataMixin, DerivedMetricsMixin, AssemblyMixin,
        WarningsCollector,
    )
else:
    from tushare_modules import (
        _VIP_MAP,
        HK_INCOME_MAP, HK_BALANCE_MAP, HK_CASHFLOW_MAP,
        US_INCOME_MAP, US_BALANCE_MAP, US_CASHFLOW_MAP,
        _YF_INCOME_MAP, _YF_BALANCE_MAP, _YF_CASHFLOW_MAP,
        InfrastructureMixin, YFinanceMixin, FinancialsMixin,
        OtherDataMixin, DerivedMetricsMixin, AssemblyMixin,
        WarningsCollector,
    )


def rate_limit(func):
    """Decorator to enforce 0.5s delay between Tushare API calls."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep(0.5)
        return func(*args, **kwargs)
    return wrapper


class TushareClient(
    InfrastructureMixin,
    YFinanceMixin,
    FinancialsMixin,
    OtherDataMixin,
    DerivedMetricsMixin,
    AssemblyMixin,
):
    """Client for Tushare Pro API with rate limiting and retry logic."""

    MAX_RETRIES = 5
    RETRY_DELAY = 2.0  # seconds between retries

    BASIC_CACHE_TTL = 7 * 86400  # 7 days in seconds

    def __init__(self, token: str, as_of: str | None = None):
        raw_as_of = str(as_of or pd.Timestamp.now().strftime("%Y%m%d")).strip()
        parsed_as_of = pd.to_datetime(raw_as_of, errors="raise")
        self.as_of = parsed_as_of.strftime("%Y%m%d")
        ts.set_token(token)
        self.pro = ts.pro_api(timeout=30)
        self.token = token
        self._store = {}  # {key: pd.DataFrame} for derived metrics computation
        self._yf_available = _yf_available
        self._cache_dir = os.path.join("output", ".collector_cache")
        self._fy_end_month: int = 12  # default: calendar year
        self._currency: str = "CNY"
        # Broker API support: route calls through custom URL + enable VIP endpoints
        api_url = get_api_url()
        self._vip_mode = bool(api_url)
        if api_url:
            self.pro._DataApi__token = token
            self.pro._DataApi__http_url = api_url

    @rate_limit
    def _safe_call(self, api_name: str, **kwargs) -> pd.DataFrame:
        """Call a Tushare API endpoint with retry logic.

        Auto-upgrades to VIP endpoints when broker is active.

        Args:
            api_name: The API endpoint name (e.g., 'stock_basic').
            **kwargs: Parameters passed to the API call.

        Returns:
            DataFrame with results.

        Raises:
            RuntimeError: After MAX_RETRIES failures.
        """
        # Auto-upgrade to VIP endpoint when broker is active
        effective_name = api_name
        if self._vip_mode and api_name in _VIP_MAP:
            effective_name = _VIP_MAP[api_name]

        last_err = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                api_func = getattr(self.pro, effective_name)
                df = api_func(**kwargs)
                return df
            except Exception as e:
                last_err = e
                if attempt < self.MAX_RETRIES:
                    is_conn_err = isinstance(e, (ConnectionError, OSError)) or \
                        "RemoteDisconnected" in type(e).__name__ or \
                        "ConnectionAborted" in str(e) or \
                        "RemoteDisconnected" in str(e)
                    if is_conn_err:
                        print(f"[retry {attempt}/{self.MAX_RETRIES}] {effective_name}: connection error, re-creating API client...", file=sys.stderr)
                        self.pro = ts.pro_api(timeout=30)
                        # Re-apply broker hacks after re-creating client
                        api_url = get_api_url()
                        if api_url:
                            self.pro._DataApi__token = self.token
                            self.pro._DataApi__http_url = api_url
                    else:
                        print(f"[retry {attempt}/{self.MAX_RETRIES}] {effective_name}: {e}", file=sys.stderr)
                    time.sleep(self.RETRY_DELAY * attempt)
        raise RuntimeError(
            f"Tushare API '{effective_name}' failed after {self.MAX_RETRIES} retries: {last_err}"
        )

    def _cached_basic_call(self, api_name: str, **kwargs) -> pd.DataFrame:
        """Call stock_basic/hk_basic with 7-day file cache."""
        ts_code = kwargs.get("ts_code", "all")
        cache_file = os.path.join(self._cache_dir, f"{api_name}_{ts_code}.json")
        if os.path.exists(cache_file):
            mtime = os.path.getmtime(cache_file)
            if time.time() - mtime < self.BASIC_CACHE_TTL:
                return pd.read_json(cache_file)
        df = self._safe_call(api_name, **kwargs)
        if not df.empty:
            os.makedirs(self._cache_dir, exist_ok=True)
            df.to_json(cache_file, orient="records", force_ascii=False)
        return df

    def _cached_us_daily(self, ts_code: str = None) -> pd.DataFrame:
        """Fetch us_daily with same-day file cache (bulk all-stock fetch).

        First call fetches ALL US stocks (limit=6000) and caches to Parquet.
        Subsequent same-day calls read from cache and filter by ts_code.
        """
        cache_file = os.path.join(self._cache_dir, f"us_daily_all_{self.as_of}.parquet")

        # The point-in-time boundary is part of the cache identity.  This makes
        # repeated historical runs deterministic without relying on file mtime.
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
            if ts_code:
                df = df[df["ts_code"] == ts_code]
            return df

        # Bulk fetch all US stocks
        df = self._safe_call("us_daily", limit=6000,
                             fields="ts_code,trade_date,open,high,low,close,"
                                    "vol,amount,pe,pb,total_mv")
        if not df.empty:
            os.makedirs(self._cache_dir, exist_ok=True)
            df.to_parquet(cache_file, index=False)

        if ts_code and not df.empty:
            df = df[df["ts_code"] == ts_code]
        return df


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect financial data from Tushare Pro API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --code 600887.SH
  %(prog)s --code 600887 --output output/data_pack_market.md
  %(prog)s --code 00700.HK --extra-fields balancesheet.defer_tax_assets
        """,
    )
    parser.add_argument(
        "--code",
        required=True,
        help="Stock code (e.g., 600887.SH, 000858.SZ, 00700.HK, or plain digits)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Tushare API token (defaults to TUSHARE_TOKEN env var)",
    )
    parser.add_argument(
        "--output",
        default="output/data_pack_market.md",
        help="Output file path (default: output/data_pack_market.md)",
    )
    parser.add_argument(
        "--extra-fields",
        nargs="*",
        help="Additional fields to fetch (format: endpoint.field_name)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print parsed arguments and exit without calling API",
    )
    parser.add_argument(
        "--refresh-market",
        action="store_true",
        help="Only refresh market-sensitive sections (§1/§2/§11/§14) in existing data pack",
    )
    parser.add_argument(
        "--as-of",
        default=None,
        help="Point-in-time boundary (YYYY-MM-DD; default: today)",
    )
    parser.add_argument(
        "--snapshot-dir",
        default=None,
        help="Snapshot directory (default: <output-dir>/data_snapshot)",
    )
    parser.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Do not persist the collected DataFrame snapshot",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Validate and normalize stock code
    try:
        ts_code = validate_stock_code(args.code)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.dry_run:
        print("=== Dry Run ===")
        print(f"  Stock code: {args.code} -> {ts_code}")
        print(f"  Token: {'provided via --token' if args.token else 'from TUSHARE_TOKEN env'}")
        print(f"  Output: {args.output}")
        print(f"  As of: {args.as_of or 'today'}")
        print(f"  Snapshot: {'disabled' if args.no_snapshot else args.snapshot_dir or 'next to output'}")
        print(f"  Extra fields: {args.extra_fields or 'none'}")
        return

    # Get token
    token = args.token or get_token()
    client = TushareClient(token, as_of=args.as_of)
    output_path = Path(args.output)
    snapshot_dir = Path(args.snapshot_dir) if args.snapshot_dir else output_path.parent / "data_snapshot"

    if args.refresh_market:
        if not output_path.exists():
            print(f"⚠️ {output_path} does not exist, falling back to full collection")
            print(f"Collecting data for {ts_code}...")
            data_pack = client.assemble_data_pack(ts_code)
        elif not snapshot_exists(snapshot_dir):
            print(f"⚠️ {snapshot_dir} does not exist; full collection is required for a complete snapshot")
            print(f"Collecting data for {ts_code}...")
            data_pack = client.assemble_data_pack(ts_code)
        else:
            existing = output_path.read_text(encoding="utf-8")
            age_days = client._check_staleness(existing)
            if age_days > 7:
                print(f"⚠️ Data pack is {age_days} days old, falling back to full collection")
                print(f"Collecting data for {ts_code}...")
                data_pack = client.assemble_data_pack(ts_code)
            else:
                store, manifest = load_snapshot(snapshot_dir)
                if manifest["ts_code"] != ts_code:
                    raise SystemExit(
                        f"Snapshot code mismatch: {manifest['ts_code']} != {ts_code}"
                    )
                if manifest["as_of"] > client.as_of:
                    raise SystemExit(
                        f"Snapshot as_of {manifest['as_of']} is later than requested {client.as_of}"
                    )
                client._store = store
                client._currency = manifest.get("currency", client._currency)
                client._fy_end_month = int(manifest.get("fy_end_month", 12))
                print(f"Refreshing market data for {ts_code} (data pack is {age_days} day(s) old)...")
                data_pack = client.refresh_market_sections(ts_code, existing)
    else:
        print(f"Collecting data for {ts_code}...")
        data_pack = client.assemble_data_pack(ts_code)

    # Handle extra fields
    if args.extra_fields:
        extra_lines = ["\n", format_header(2, "附加字段"), ""]
        for field_spec in args.extra_fields:
            parts = field_spec.split(".", 1)
            if len(parts) != 2:
                extra_lines.append(f"- 无效字段格式: {field_spec} (应为 endpoint.field_name)")
                continue
            endpoint, field_name = parts
            try:
                df = client._safe_call(endpoint, ts_code=ts_code, fields=f"ts_code,end_date,{field_name}")
                if not df.empty:
                    extra_lines.append(f"**{endpoint}.{field_name}**:")
                    extra_lines.append(df.to_markdown(index=False))
                    extra_lines.append("")
                else:
                    extra_lines.append(f"- {endpoint}.{field_name}: 无数据")
            except Exception as e:
                extra_lines.append(f"- {endpoint}.{field_name}: 获取失败 ({e})")
        data_pack += "\n".join(extra_lines)

    # Write output
    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(data_pack)
    if not args.no_snapshot:
        manifest_path = save_snapshot(
            client._store,
            snapshot_dir,
            ts_code=ts_code,
            as_of=client.as_of,
            currency=client._currency,
            fy_end_month=client._fy_end_month,
        )
        print(f"Snapshot written to {manifest_path}")
    print(f"Output written to {args.output}")
    print(f"File size: {os.path.getsize(args.output):,} bytes")


if __name__ == "__main__":
    main()
