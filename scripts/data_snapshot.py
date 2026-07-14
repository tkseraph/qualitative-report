"""Persistent, versioned snapshots for a single-stock data collection run."""

from __future__ import annotations

import json
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


SNAPSHOT_SCHEMA_VERSION = 1
MANIFEST_NAME = "manifest.json"


class SnapshotError(RuntimeError):
    """Raised when a snapshot is missing, incompatible, or malformed."""


def _json_value(value: Any) -> Any:
    """Convert common scalar/container values to JSON-compatible values."""
    if isinstance(value, dict):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_value(value.item())
        except (TypeError, ValueError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported snapshot value: {type(value).__name__}")


def snapshot_exists(snapshot_dir: str | os.PathLike[str]) -> bool:
    return (Path(snapshot_dir) / MANIFEST_NAME).is_file()


def save_snapshot(
    store: dict[str, Any],
    snapshot_dir: str | os.PathLike[str],
    *,
    ts_code: str,
    as_of: str,
    currency: str,
    fy_end_month: int,
) -> Path:
    """Persist DataFrames as Parquet and small values in the manifest.

    Data files are replaced atomically one by one and the manifest is replaced
    last, so readers never observe a manifest pointing at a partially written
    snapshot.
    """
    target = Path(snapshot_dir)
    target.mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict[str, Any]] = {}
    generation = uuid.uuid4().hex
    generation_dir = target / "data" / generation
    generation_dir.mkdir(parents=True, exist_ok=False)

    for index, (key, value) in enumerate(sorted(store.items())):
        if isinstance(value, pd.DataFrame):
            relative_path = Path("data") / generation / f"{index:03d}.parquet"
            final_path = target / relative_path
            temp_path = generation_dir / f".{index:03d}.parquet.tmp"
            value.to_parquet(temp_path, index=False)
            os.replace(temp_path, final_path)
            entries[key] = {
                "kind": "dataframe",
                "file": relative_path.as_posix(),
                "rows": int(len(value)),
                "columns": [str(c) for c in value.columns],
            }
            continue
        try:
            entries[key] = {"kind": "json", "value": _json_value(value)}
        except TypeError:
            # Runtime-only helpers should not make the durable dataset fail.
            continue

    manifest = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "ts_code": ts_code,
        "as_of": str(as_of),
        "currency": currency,
        "fy_end_month": int(fy_end_month),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entries": entries,
    }
    manifest_path = target / MANIFEST_NAME
    temp_manifest = target / f".{MANIFEST_NAME}.tmp"
    temp_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temp_manifest, manifest_path)
    return manifest_path


def load_snapshot(
    snapshot_dir: str | os.PathLike[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load and validate a snapshot store plus its manifest metadata."""
    target = Path(snapshot_dir)
    manifest_path = target / MANIFEST_NAME
    if not manifest_path.is_file():
        raise SnapshotError(f"snapshot manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"invalid snapshot manifest: {exc}") from exc

    if manifest.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise SnapshotError(
            "unsupported snapshot schema version: "
            f"{manifest.get('schema_version')!r}"
        )
    if not manifest.get("ts_code") or not manifest.get("as_of"):
        raise SnapshotError("snapshot manifest is missing ts_code/as_of")

    store: dict[str, Any] = {}
    for key, entry in manifest.get("entries", {}).items():
        kind = entry.get("kind")
        if kind == "json":
            store[key] = entry.get("value")
            continue
        if kind != "dataframe":
            raise SnapshotError(f"unknown snapshot entry kind for {key}: {kind!r}")
        filename = entry.get("file")
        relative_path = Path(filename) if isinstance(filename, str) else Path("/")
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise SnapshotError(f"unsafe snapshot path for {key}: {filename!r}")
        data_path = target / relative_path
        if not data_path.is_file():
            raise SnapshotError(f"snapshot data missing for {key}: {data_path}")
        store[key] = pd.read_parquet(data_path)

    return store, manifest
