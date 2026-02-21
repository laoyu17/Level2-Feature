from __future__ import annotations

import time

import polars as pl

from l2_features.features.engine import compute_features_batch


def test_perf_smoke_batch(sample_csv_path) -> None:
    df = pl.read_csv(sample_csv_path).head(5000)

    start = time.perf_counter()
    out = compute_features_batch(df, keep_raw=False)
    elapsed = time.perf_counter() - start

    throughput = out.height / elapsed if elapsed > 0 else 0.0
    assert throughput > 1000
