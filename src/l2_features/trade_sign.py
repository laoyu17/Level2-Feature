from __future__ import annotations

from typing import Any

import polars as pl

_BUY_TOKENS = {"b", "buy", "1", "+1"}
_SELL_TOKENS = {"s", "sell", "-1"}
_NEUTRAL_TOKENS = {"0"}


def _normalize_numeric_sign(value: float) -> float | None:
    if abs(value - 1.0) <= 1e-12:
        return 1.0
    if abs(value + 1.0) <= 1e-12:
        return -1.0
    if abs(value) <= 1e-12:
        return 0.0
    return None


def parse_trade_side_value(value: Any) -> float | None:
    """将输入 side 解析为 -1/0/1；无法识别时返回 None。"""

    if value is None:
        return None

    if isinstance(value, str):
        token = value.strip().lower()
        if not token:
            return None
        if token in _BUY_TOKENS:
            return 1.0
        if token in _SELL_TOKENS:
            return -1.0
        if token in _NEUTRAL_TOKENS:
            return 0.0
        try:
            numeric = float(token)
        except ValueError:
            return None
        return _normalize_numeric_sign(numeric)

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    return _normalize_numeric_sign(numeric)


def trade_side_sign_expr(column: str = "side") -> pl.Expr:
    """Polars 表达式版本的 side 解析逻辑，未知值返回 null。"""

    text_expr = pl.col(column).cast(pl.Utf8, strict=False).str.strip_chars().str.to_lowercase()
    numeric_expr = text_expr.cast(pl.Float64, strict=False)

    numeric_sign = (
        pl.when((numeric_expr - 1.0).abs() <= 1e-12)
        .then(1.0)
        .when((numeric_expr + 1.0).abs() <= 1e-12)
        .then(-1.0)
        .when(numeric_expr.abs() <= 1e-12)
        .then(0.0)
        .otherwise(None)
    )

    return (
        pl.when(text_expr.is_in(list(_BUY_TOKENS)))
        .then(1.0)
        .when(text_expr.is_in(list(_SELL_TOKENS)))
        .then(-1.0)
        .when(text_expr.is_in(list(_NEUTRAL_TOKENS)))
        .then(0.0)
        .otherwise(numeric_sign)
    )
