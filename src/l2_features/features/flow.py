from __future__ import annotations

import polars as pl


def _safe_div(num: pl.Expr, den: pl.Expr, default: float = 0.0) -> pl.Expr:
    return pl.when(den.abs() > 1e-12).then(num / den).otherwise(default)


def flow_feature_exprs() -> list[pl.Expr]:
    prev_bid_px = pl.col("bid_px_1").shift(1).over("symbol")
    prev_ask_px = pl.col("ask_px_1").shift(1).over("symbol")
    prev_bid_sz = pl.col("bid_sz_1").shift(1).over("symbol")
    prev_ask_sz = pl.col("ask_sz_1").shift(1).over("symbol")

    bid_add = (pl.col("bid_sz_1") - prev_bid_sz).clip(lower_bound=0.0)
    ask_add = (pl.col("ask_sz_1") - prev_ask_sz).clip(lower_bound=0.0)
    bid_cancel = (prev_bid_sz - pl.col("bid_sz_1")).clip(lower_bound=0.0)
    ask_cancel = (prev_ask_sz - pl.col("ask_sz_1")).clip(lower_bound=0.0)

    ofi = (
        pl.when(pl.col("bid_px_1") >= prev_bid_px)
        .then(pl.col("bid_sz_1"))
        .otherwise(0.0)
        - pl.when(pl.col("bid_px_1") <= prev_bid_px)
        .then(prev_bid_sz)
        .otherwise(0.0)
        - pl.when(pl.col("ask_px_1") <= prev_ask_px)
        .then(pl.col("ask_sz_1"))
        .otherwise(0.0)
        + pl.when(pl.col("ask_px_1") >= prev_ask_px)
        .then(prev_ask_sz)
        .otherwise(0.0)
    )

    cancel_total = bid_cancel + ask_cancel
    add_total = bid_add + ask_add

    return [
        ofi.alias("order_flow_imbalance"),
        _safe_div(cancel_total, prev_bid_sz + prev_ask_sz).alias("cancel_intensity"),
        _safe_div(add_total, cancel_total + 1e-9).alias("add_cancel_ratio"),
        bid_cancel.alias("bid_cancel"),
        ask_cancel.alias("ask_cancel"),
    ]
