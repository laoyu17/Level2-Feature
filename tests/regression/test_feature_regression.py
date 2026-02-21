from __future__ import annotations

import polars as pl

from l2_features.features.engine import compute_features_batch


def test_feature_regression_snapshot(sample_csv_path) -> None:
    df = pl.read_csv(sample_csv_path).head(5)
    out = compute_features_batch(df, keep_raw=False)

    cols = ["obi_l1", "spread_abs", "microprice", "order_flow_imbalance"]
    snapshot = out.select(cols).to_dicts()

    expected = [
        {
            "obi_l1": 0.172501,
            "spread_abs": 0.024401,
            "microprice": 10.002941,
            "order_flow_imbalance": 0.0,
        },
        {
            "obi_l1": 0.220488,
            "spread_abs": 0.026555,
            "microprice": 10.005317,
            "order_flow_imbalance": 4419.0,
        },
        {
            "obi_l1": -0.352247,
            "spread_abs": 0.024733,
            "microprice": 9.99926,
            "order_flow_imbalance": 2926.0,
        },
        {
            "obi_l1": 0.534273,
            "spread_abs": 0.03424,
            "microprice": 10.015701,
            "order_flow_imbalance": 1254.0,
        },
        {
            "obi_l1": 0.202916,
            "spread_abs": 0.030855,
            "microprice": 10.011167,
            "order_flow_imbalance": 1169.0,
        },
    ]

    rounded = [
        {
            k: round(float(v), 6)
            for k, v in row.items()
        }
        for row in snapshot
    ]

    assert rounded == expected
