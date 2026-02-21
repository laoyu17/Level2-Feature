from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from l2_features.features.engine import compute_features_batch
from l2_features.stream.updater import StreamFeatureUpdater


def test_batch_stream_core_columns_consistent(sample_csv_path: Path) -> None:
    df = pl.read_csv(sample_csv_path).head(300)
    batch = compute_features_batch(df, keep_raw=False)

    updater = StreamFeatureUpdater()
    stream = pl.DataFrame([updater.update(row) for row in df.iter_rows(named=True)])

    shared_columns = [
        "mid_px",
        "spread_abs",
        "spread_bps",
        "obi_l1",
        "obi_l5",
        "obi_l10",
        "depth_ratio_l10",
        "microprice",
        "ask_slope",
        "bid_slope",
        "book_slope",
        "bid_depth_l10",
        "ask_depth_l10",
        "order_flow_imbalance",
        "cancel_intensity",
        "add_cancel_ratio",
        "bid_cancel",
        "ask_cancel",
        "trade_sign",
        "trade_sign_imbalance_20",
        "signed_turnover",
        "turnover",
        "instant_impact",
        "amihud_proxy",
        "log_return",
        "rv_20",
        "rv_100",
        "rv_500",
    ]
    for col in shared_columns:
        left = np.array(batch[col].to_list(), dtype=np.float64)
        right = np.array(stream[col].to_list(), dtype=np.float64)
        assert np.allclose(left, right, atol=1e-12), f"column mismatch: {col}"


def test_batch_stream_trade_sign_consistent_with_string_side() -> None:
    df = pl.DataFrame(
        {
            "ts": [1, 2, 3, 4],
            "symbol": ["000001.SZ"] * 4,
            "event_type": ["trade"] * 4,
            "last_px": [10.0, 9.99, 10.02, 10.03],
            "last_sz": [100.0] * 4,
            "bid_px_1": [9.99] * 4,
            "bid_sz_1": [2000.0] * 4,
            "ask_px_1": [10.01] * 4,
            "ask_sz_1": [2100.0] * 4,
            "side": ["BUY", "S", "UNKNOWN", "0"],
        }
    )

    batch = compute_features_batch(df, keep_raw=False)
    updater = StreamFeatureUpdater()
    stream = pl.DataFrame([updater.update(row) for row in df.iter_rows(named=True)])

    assert np.allclose(
        np.array(batch["trade_sign"].to_list(), dtype=np.float64),
        np.array(stream["trade_sign"].to_list(), dtype=np.float64),
        atol=1e-12,
    )
