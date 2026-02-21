from __future__ import annotations

import polars as pl
import pytest

from l2_features.schema import detect_depth_levels, validate_required_columns


def test_validate_required_columns_ok() -> None:
    df = pl.DataFrame(
        {
            "ts": [1],
            "symbol": ["000001.SZ"],
            "event_type": ["quote"],
            "last_px": [10.0],
            "last_sz": [1000.0],
            "bid_px_1": [9.99],
            "bid_sz_1": [3000.0],
            "ask_px_1": [10.01],
            "ask_sz_1": [2800.0],
        }
    )

    validate_required_columns(df)


def test_validate_required_columns_missing() -> None:
    df = pl.DataFrame(
        {
            "ts": [1],
            "symbol": ["000001.SZ"],
            "event_type": ["quote"],
            "last_px": [10.0],
            "last_sz": [1000.0],
            "bid_px_1": [9.99],
            "ask_px_1": [10.01],
            "ask_sz_1": [2800.0],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_required_columns(df)


def test_detect_depth_levels() -> None:
    depth = detect_depth_levels(["bid_px_1", "ask_px_1", "bid_px_5", "ask_px_5"])
    assert depth == 5
