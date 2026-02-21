from __future__ import annotations

from collections.abc import Iterable

import polars as pl

from l2_features.features.book import order_book_feature_exprs
from l2_features.features.flow import flow_feature_exprs
from l2_features.features.trade import trade_feature_exprs
from l2_features.features.volatility import log_return_expr, realized_volatility_exprs
from l2_features.schema import detect_depth_levels, normalize_dtypes, validate_required_columns

DEFAULT_VOL_WINDOWS = (20, 100, 500)

BASE_COLUMNS = ["ts", "symbol", "event_type"]
FEATURE_COLUMNS = [
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
]


def _fill_numeric_nulls(df: pl.DataFrame) -> pl.DataFrame:
    numeric_cols = [
        name
        for name, dtype in df.schema.items()
        if dtype.is_numeric() and name != "ts"
    ]
    return df.with_columns([pl.col(c).fill_null(0.0).fill_nan(0.0) for c in numeric_cols])


def compute_features_batch(
    data: pl.DataFrame | pl.LazyFrame,
    *,
    depth_levels: int = 10,
    volatility_windows: tuple[int, ...] = DEFAULT_VOL_WINDOWS,
    selected_features: Iterable[str] | None = None,
    keep_raw: bool = True,
) -> pl.DataFrame:
    """批处理计算 Level2 微观结构特征。"""

    df = data.collect(engine="streaming") if isinstance(data, pl.LazyFrame) else data

    validate_required_columns(df)
    df = normalize_dtypes(df)

    effective_depth = min(depth_levels, detect_depth_levels(df.columns))
    has_side = "side" in df.columns

    out = df.sort(["symbol", "ts"])
    out = out.with_columns(order_book_feature_exprs(effective_depth))
    out = out.with_columns(flow_feature_exprs())
    out = out.with_columns(trade_feature_exprs(has_side))
    out = out.with_columns(log_return_expr())
    out = out.with_columns(realized_volatility_exprs(volatility_windows))

    feature_columns = FEATURE_COLUMNS + [f"rv_{w}" for w in volatility_windows]

    out = _fill_numeric_nulls(out)

    chosen_features = list(selected_features) if selected_features else feature_columns
    missing = sorted([f for f in chosen_features if f not in out.columns])
    if missing:
        raise ValueError(f"Unknown features requested: {missing}")

    if keep_raw:
        return out

    selected = [c for c in BASE_COLUMNS if c in out.columns] + chosen_features
    return out.select(selected)
