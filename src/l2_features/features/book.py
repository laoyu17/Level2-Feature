from __future__ import annotations

import polars as pl


def _safe_div(num: pl.Expr, den: pl.Expr, default: float = 0.0) -> pl.Expr:
    return pl.when(den.abs() > 1e-12).then(num / den).otherwise(default)


def _depth_sum_expr(prefix: str, depth_levels: int) -> pl.Expr:
    cols = [pl.col(f"{prefix}_{i}") for i in range(1, depth_levels + 1)]
    return pl.sum_horizontal(cols)


def _depth_weighted_price_distance(side: str, depth_levels: int) -> pl.Expr:
    if side == "ask":
        deltas = [
            (pl.col(f"ask_px_{i}") - pl.col("ask_px_1")) * pl.col(f"ask_sz_{i}")
            for i in range(1, depth_levels + 1)
        ]
        denom = _depth_sum_expr("ask_sz", depth_levels)
    else:
        deltas = [
            (pl.col("bid_px_1") - pl.col(f"bid_px_{i}")) * pl.col(f"bid_sz_{i}")
            for i in range(1, depth_levels + 1)
        ]
        denom = _depth_sum_expr("bid_sz", depth_levels)

    return _safe_div(pl.sum_horizontal(deltas), denom)


def order_book_feature_exprs(depth_levels: int) -> list[pl.Expr]:
    levels_5 = min(depth_levels, 5)
    levels_10 = min(depth_levels, 10)

    bid_depth_5 = _depth_sum_expr("bid_sz", levels_5)
    ask_depth_5 = _depth_sum_expr("ask_sz", levels_5)
    bid_depth_10 = _depth_sum_expr("bid_sz", levels_10)
    ask_depth_10 = _depth_sum_expr("ask_sz", levels_10)

    spread_abs = (pl.col("ask_px_1") - pl.col("bid_px_1")).alias("spread_abs")
    mid_px = ((pl.col("ask_px_1") + pl.col("bid_px_1")) * 0.5).alias("mid_px")

    return [
        mid_px,
        spread_abs,
        _safe_div(pl.col("ask_px_1") - pl.col("bid_px_1"), pl.col("bid_px_1")).alias("spread_bps"),
        _safe_div(
            pl.col("bid_sz_1") - pl.col("ask_sz_1"),
            pl.col("bid_sz_1") + pl.col("ask_sz_1"),
        ).alias("obi_l1"),
        _safe_div(bid_depth_5 - ask_depth_5, bid_depth_5 + ask_depth_5).alias("obi_l5"),
        _safe_div(bid_depth_10 - ask_depth_10, bid_depth_10 + ask_depth_10).alias("obi_l10"),
        _safe_div(bid_depth_10, ask_depth_10).alias("depth_ratio_l10"),
        _safe_div(
            pl.col("ask_px_1") * pl.col("bid_sz_1") + pl.col("bid_px_1") * pl.col("ask_sz_1"),
            pl.col("bid_sz_1") + pl.col("ask_sz_1"),
        ).alias("microprice"),
        _depth_weighted_price_distance("ask", levels_10).alias("ask_slope"),
        _depth_weighted_price_distance("bid", levels_10).alias("bid_slope"),
        (
            _depth_weighted_price_distance("ask", levels_10)
            + _depth_weighted_price_distance("bid", levels_10)
        ).alias("book_slope"),
        bid_depth_10.alias("bid_depth_l10"),
        ask_depth_10.alias("ask_depth_l10"),
    ]
