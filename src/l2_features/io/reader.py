from __future__ import annotations

from pathlib import Path

import polars as pl

from l2_features.schema import normalize_dtypes, validate_required_columns


def read_level2(path: str | Path, *, lazy: bool = False) -> pl.DataFrame | pl.LazyFrame:
    """读取 Level2/Tick 数据，自动识别 csv/parquet。"""

    data_path = Path(path)
    suffix = data_path.suffix.lower()

    if suffix == ".parquet":
        frame = pl.scan_parquet(data_path) if lazy else pl.read_parquet(data_path)
    elif suffix in {".csv", ".txt"}:
        frame = pl.scan_csv(data_path) if lazy else pl.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path}")

    if lazy:
        validate_required_columns(frame)
        return frame

    validate_required_columns(frame)
    return normalize_dtypes(frame)


def read_level2_with_filters(
    path: str | Path,
    *,
    symbol: str | None = None,
    ts_start: int | None = None,
    ts_end: int | None = None,
) -> pl.DataFrame:
    lf = read_level2(path, lazy=True)
    assert isinstance(lf, pl.LazyFrame)

    if symbol:
        lf = lf.filter(pl.col("symbol") == symbol)
    if ts_start is not None:
        lf = lf.filter(pl.col("ts") >= ts_start)
    if ts_end is not None:
        lf = lf.filter(pl.col("ts") <= ts_end)

    df = lf.collect(engine="streaming")
    return normalize_dtypes(df)
