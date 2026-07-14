"""Tests for point-in-time selection and durable data snapshots."""

import json
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_snapshot import SnapshotError, load_snapshot, save_snapshot
from tushare_collector import TushareClient


def _client(as_of="2025-03-31"):
    with patch("tushare_collector.ts") as mock_ts:
        mock_ts.pro_api.return_value = MagicMock()
        return TushareClient("test", as_of=as_of)


def test_client_normalizes_as_of():
    assert _client("2025-03-31").as_of == "20250331"


def test_vintage_excludes_later_announcements_and_revisions():
    client = _client("2025-03-31")
    source = pd.DataFrame([
        {
            "end_date": "20241231",
            "ann_date": "20250320",
            "f_ann_date": "20250320",
            "update_flag": "0",
            "revenue": 100,
        },
        {
            "end_date": "20241231",
            "ann_date": "20250420",
            "f_ann_date": "20250420",
            "update_flag": "1",
            "revenue": 120,
        },
        {
            "end_date": "20231231",
            "ann_date": "20240420",
            "f_ann_date": "20240420",
            "update_flag": "0",
            "revenue": 90,
        },
        {
            "end_date": "20250630",
            "ann_date": "20250820",
            "f_ann_date": "20250820",
            "update_flag": "0",
            "revenue": 130,
        },
    ])

    selected = client._select_vintage(source)

    assert list(selected["end_date"]) == ["20241231", "20231231"]
    assert selected.iloc[0]["revenue"] == 100


def test_snapshot_round_trip(tmp_path):
    store = {
        "income": pd.DataFrame([
            {"end_date": "20241231", "revenue": 100.0},
            {"end_date": "20231231", "revenue": 90.0},
        ]),
        "income_years": ["2024", "2023"],
        "factor3_sensitivity": {"aa_selected": 42.5},
    }
    snapshot_dir = tmp_path / "snapshot"

    manifest_path = save_snapshot(
        store,
        snapshot_dir,
        ts_code="600887.SH",
        as_of="20250331",
        currency="CNY",
        fy_end_month=12,
    )
    restored, manifest = load_snapshot(snapshot_dir)

    assert manifest_path.is_file()
    assert manifest["schema_version"] == 1
    assert manifest["as_of"] == "20250331"
    pd.testing.assert_frame_equal(restored["income"], store["income"])
    assert restored["income_years"] == ["2024", "2023"]
    assert restored["factor3_sensitivity"]["aa_selected"] == 42.5


def test_snapshot_rejects_unknown_schema(tmp_path):
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    (snapshot_dir / "manifest.json").write_text(
        json.dumps({"schema_version": 999, "ts_code": "X", "as_of": "20250101"}),
        encoding="utf-8",
    )

    with pytest.raises(SnapshotError, match="schema version"):
        load_snapshot(snapshot_dir)
