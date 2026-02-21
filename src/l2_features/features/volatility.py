from __future__ import annotations

import math

import polars as pl


def log_return_expr() -> pl.Expr:
    prev_px = pl.col("last_px").shift(1).over("symbol")
    return (pl.col("last_px") / prev_px).log().alias("log_return")


def realized_volatility_exprs(windows: tuple[int, ...] = (20, 100, 500)) -> list[pl.Expr]:
    return [
        (
            pl.col("log_return").rolling_std(window_size=w).over("symbol") * math.sqrt(w)
        ).alias(f"rv_{w}")
        for w in windows
    ]
