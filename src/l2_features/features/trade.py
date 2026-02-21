from __future__ import annotations

import polars as pl


def _safe_div(num: pl.Expr, den: pl.Expr, default: float = 0.0) -> pl.Expr:
    return pl.when(den.abs() > 1e-12).then(num / den).otherwise(default)


def trade_feature_exprs(has_side: bool) -> list[pl.Expr]:
    prev_last_px = pl.col("last_px").shift(1).over("symbol")

    if has_side:
        sign_expr = pl.col("side").cast(pl.Float64)
    else:
        sign_expr = (
            pl.when(pl.col("last_px") > prev_last_px)
            .then(1.0)
            .when(pl.col("last_px") < prev_last_px)
            .then(-1.0)
            .otherwise(0.0)
        )

    signed_turnover = (sign_expr * pl.col("last_px") * pl.col("last_sz")).alias("signed_turnover")
    turnover = (pl.col("last_px") * pl.col("last_sz")).alias("turnover")

    return [
        sign_expr.alias("trade_sign"),
        sign_expr.rolling_mean(window_size=20).over("symbol").alias("trade_sign_imbalance_20"),
        signed_turnover,
        turnover,
        _safe_div(
            (pl.col("last_px") - pl.col("mid_px")).abs(),
            pl.col("mid_px"),
        ).alias("instant_impact"),
        _safe_div(
            (pl.col("last_px") / prev_last_px).log().abs(),
            pl.col("last_sz") + 1e-9,
        ).alias("amihud_proxy"),
    ]
