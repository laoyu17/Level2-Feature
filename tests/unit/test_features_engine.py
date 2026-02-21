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
