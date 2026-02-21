from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from l2_features.schema import normalize_dtypes, validate_required_columns


@dataclass(slots=True)
class AdapterRule:
    source: str
    target: str


DEFAULT_COLUMN_ALIASES: tuple[AdapterRule, ...] = (
    AdapterRule("timestamp", "ts"),
    AdapterRule("code", "symbol"),
    AdapterRule("instrument", "symbol"),
    AdapterRule("trade_price", "last_px"),
    AdapterRule("trade_size", "last_sz"),
    AdapterRule("type", "event_type"),
)


def apply_aliases(
    df: pl.DataFrame,
    rules: tuple[AdapterRule, ...] = DEFAULT_COLUMN_ALIASES,
) -> pl.DataFrame:
    rename_map: dict[str, str] = {}
    for rule in rules:
        if rule.source in df.columns and rule.target not in df.columns:
            rename_map[rule.source] = rule.target

    if rename_map:
        df = df.rename(rename_map)
    return df


def canonicalize_level2(df: pl.DataFrame) -> pl.DataFrame:
    """将不同源字段名适配为项目标准 schema。"""

    out = apply_aliases(df)
    validate_required_columns(out)
    return normalize_dtypes(out)
