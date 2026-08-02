#!/usr/bin/env python3
"""Shared Parquet-backed disk cache utilities."""

from __future__ import annotations

import hashlib
import os
import time

import pandas as pd


class ScreenerCache:
    """Small DataFrame disk cache with per-read TTL control.

    Cache failures are deliberately non-fatal: callers can always fall back to
    the source API if Parquet support or an individual cache entry is broken.
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    @staticmethod
    def _digest(key: str) -> str:
        return hashlib.md5(key.encode("utf-8")).hexdigest()

    def _path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{self._digest(key)}.parquet")

    def _meta_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{self._digest(key)}.meta")

    def get(self, key: str, ttl_seconds: int) -> pd.DataFrame | None:
        """Return a cached DataFrame when present and still within its TTL."""
        path = self._path(key)
        meta_path = self._meta_path(key)
        if not os.path.exists(path) or not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, encoding="utf-8") as handle:
                created_at = float(handle.readline().strip())
            if time.time() - created_at > ttl_seconds:
                return None
            return pd.read_parquet(path)
        except Exception:
            return None

    def put(self, key: str, df: pd.DataFrame) -> None:
        """Store a DataFrame and the original key used for invalidation."""
        try:
            df.to_parquet(self._path(key), index=False)
            with open(self._meta_path(key), "w", encoding="utf-8") as handle:
                handle.write(f"{time.time()}\n{key}")
        except Exception:
            pass

    def invalidate(self, key: str) -> None:
        """Remove one cache entry if it exists."""
        for path in (self._path(key), self._meta_path(key)):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove entries whose original cache keys start with ``prefix``."""
        if not os.path.isdir(self.cache_dir):
            return
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith(".meta"):
                continue
            meta_path = os.path.join(self.cache_dir, filename)
            try:
                with open(meta_path, encoding="utf-8") as handle:
                    lines = handle.read().splitlines()
                original_key = lines[1] if len(lines) > 1 else ""
                if original_key.startswith(prefix):
                    os.remove(meta_path)
                    parquet_path = meta_path.removesuffix(".meta") + ".parquet"
                    try:
                        os.remove(parquet_path)
                    except FileNotFoundError:
                        pass
            except Exception:
                pass

    def clear(self) -> None:
        """Remove every regular file in this cache directory."""
        if not os.path.isdir(self.cache_dir):
            return
        for filename in os.listdir(self.cache_dir):
            path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except FileNotFoundError:
                    pass
