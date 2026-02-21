from __future__ import annotations

import polars as pl

from l2_features.features.engine import compute_features_batch


def test_compute_features_batch_basic(sample_csv_path) -> None:
    df = pl.read_csv(sample_csv_path).head(200)
    out = compute_features_batch(df, keep_raw=False)

    assert out.height == 200
    required = {
        "mid_px",
        "obi_l1",
        "order_flow_imbalance",
        "instant_impact",
        "rv_20",
    }
    assert required.issubset(set(out.columns))
    assert out.select(pl.col("obi_l1").is_null().sum()).item() == 0


def test_compute_features_selected_features(sample_csv_path) -> None:
    df = pl.read_csv(sample_csv_path).head(100)
    out = compute_features_batch(df, selected_features=["obi_l1", "spread_abs"], keep_raw=False)

    assert out.columns == ["ts", "symbol", "event_type", "obi_l1", "spread_abs"]


def test_add_cancel_ratio_when_no_cancel_is_zero() -> None:
    df = pl.DataFrame(
        {
            "ts": [1, 2],
            "symbol": ["000001.SZ", "000001.SZ"],
            "event_type": ["quote", "quote"],
            "last_px": [10.0, 10.01],
            "last_sz": [100.0, 100.0],
            "bid_px_1": [9.99, 10.0],
            "bid_sz_1": [1000.0, 1100.0],
            "ask_px_1": [10.01, 10.02],
            "ask_sz_1": [1200.0, 1300.0],
        }
    )
    out = compute_features_batch(df, keep_raw=False)

    assert out["add_cancel_ratio"][1] == 0.0


def test_trade_sign_parses_string_side_with_fallback() -> None:
    df = pl.DataFrame(
        {
            "ts": [1, 2, 3, 4, 5],
            "symbol": ["000001.SZ"] * 5,
            "event_type": ["trade"] * 5,
            "last_px": [10.0, 10.1, 10.0, 10.1, 10.2],
            "last_sz": [100.0] * 5,
            "bid_px_1": [9.99] * 5,
            "bid_sz_1": [1000.0] * 5,
            "ask_px_1": [10.01] * 5,
            "ask_sz_1": [1200.0] * 5,
            "side": ["B", "S", "BUY", "SELL", "UNKNOWN"],
        }
    )

    out = compute_features_batch(df, keep_raw=False)

    assert out["trade_sign"].to_list() == [1.0, -1.0, 1.0, -1.0, 1.0]
