from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

MIN_REQUIRED_COLUMNS = (
    "ts",
    "symbol",
    "bid_px_1",
    "bid_sz_1",
    "ask_px_1",
    "ask_sz_1",
    "last_px",
    "last_sz",
    "event_type",
)

OPTIONAL_COLUMNS = ("side",)

REQUIRED_COLUMNS = MIN_REQUIRED_COLUMNS
DEPTH_PREFIXES = ("bid_px", "bid_sz", "ask_px", "ask_sz")


@dataclass(slots=True)
class FeatureConfig:
    """配置批处理或流式计算行为。"""

    depth_levels: int = 10
    volatility_windows: tuple[int, ...] = (20, 100, 500)
    default_symbol: str | None = None


@dataclass(slots=True)
class BookSnapshot:
    ts: int
    symbol: str
    bids: list[tuple[float, float]]
    asks: list[tuple[float, float]]


@dataclass(slots=True)
class TradeEvent:
    ts: int
    symbol: str
    last_px: float
    last_sz: float
    side: int | None = None


@dataclass(slots=True)
class FeatureVector:
    ts: int
    symbol: str
    values: dict[str, float]


def level_columns(depth_levels: int) -> tuple[str, ...]:
    cols: list[str] = []
    for i in range(1, depth_levels + 1):
        cols.extend((f"bid_px_{i}", f"bid_sz_{i}", f"ask_px_{i}", f"ask_sz_{i}"))
    return tuple(cols)


def required_columns(depth_levels: int = 1) -> tuple[str, ...]:
    base = list(MIN_REQUIRED_COLUMNS)
    if depth_levels > 1:
        base.extend(level_columns(depth_levels)[4:])
    return tuple(base)


def _depth_presence_map(columns: set[str]) -> dict[int, set[str]]:
    present: dict[int, set[str]] = {}
    for col in columns:
        for prefix in DEPTH_PREFIXES:
            token = f"{prefix}_"
            if col.startswith(token):
                suffix = col[len(token) :]
                if suffix.isdigit():
                    level = int(suffix)
                    present.setdefault(level, set()).add(prefix)
                break
    return present


def validate_depth_layout(columns: list[str] | tuple[str, ...] | set[str]) -> None:
    """校验 L2+ 深度列是否完整且连续。"""

    column_set = set(columns)
    present = _depth_presence_map(column_set)
    expected_prefixes = set(DEPTH_PREFIXES)

    for level in sorted(level for level in present if level > 1):
        prefixes = present[level]
        if prefixes != expected_prefixes:
            missing = sorted(f"{prefix}_{level}" for prefix in (expected_prefixes - prefixes))
            raise ValueError(
                f"Incomplete depth columns at level {level}, missing columns: {missing}"
            )

    if not present:
        return

    max_level = max(present)
    for level in range(2, max_level + 1):
        if level not in present:
            raise ValueError(f"Depth levels must be contiguous, missing level {level}")


def detect_depth_levels(columns: list[str] | tuple[str, ...]) -> int:
    """从列名推断当前快照支持的盘口档位数。"""

    column_set = set(columns)
    depth = 1
    level = 2
    while True:
        required = {f"{prefix}_{level}" for prefix in DEPTH_PREFIXES}
        if required.issubset(column_set):
            depth = level
            level += 1
            continue
        break
    return depth


def validate_required_columns(
    df: pl.DataFrame | pl.LazyFrame,
    depth_levels: int = 1,
    *,
    allow_optional: bool = True,
) -> None:
    """校验 Level2 数据关键列，缺失时抛出异常。"""

    schema: dict[str, Any] = df.collect_schema() if isinstance(df, pl.LazyFrame) else df.schema
    columns = set(schema.keys())
    expected = set(required_columns(depth_levels))
    if allow_optional:
        expected -= set(OPTIONAL_COLUMNS)

    missing = sorted(expected - columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    validate_depth_layout(columns)


def normalize_dtypes(df: pl.DataFrame) -> pl.DataFrame:
    """统一核心字段类型，避免后续计算出现隐式转换。"""

    cast_exprs = [
        pl.col("ts").cast(pl.Int64),
        pl.col("symbol").cast(pl.Utf8),
        pl.col("event_type").cast(pl.Utf8),
        pl.col("last_px").cast(pl.Float64),
        pl.col("last_sz").cast(pl.Float64),
    ]

    if "side" in df.columns:
        cast_exprs.append(pl.col("side").cast(pl.Utf8))

    for name in df.columns:
        if name.startswith(("bid_px_", "ask_px_", "bid_sz_", "ask_sz_")):
            cast_exprs.append(pl.col(name).cast(pl.Float64))

    return df.with_columns(cast_exprs)
