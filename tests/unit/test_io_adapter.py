from __future__ import annotations

import polars as pl

from l2_features.io.adapter import canonicalize_level2


def test_canonicalize_aliases() -> None:
    df = pl.DataFrame(
        {
            "timestamp": [1],
            "code": ["000001.SZ"],
            "type": ["quote"],
            "trade_price": [10.0],
            "trade_size": [500.0],
            "bid_px_1": [9.99],
            "bid_sz_1": [2000.0],
            "ask_px_1": [10.01],
            "ask_sz_1": [2100.0],
        }
    )

    out = canonicalize_level2(df)
    assert "ts" in out.columns
    assert "symbol" in out.columns
    assert out.height == 1
