from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from l2_features.features.engine import compute_features_batch
from l2_features.io.reader import read_level2_with_filters
from l2_features.stream.updater import StreamFeatureUpdater


def _run_batch(df: pl.DataFrame) -> tuple[int, float]:
    start = time.perf_counter()
    out = compute_features_batch(df, keep_raw=False)
    elapsed = time.perf_counter() - start
    return out.height, elapsed


def _run_stream(df: pl.DataFrame) -> tuple[int, float]:
    updater = StreamFeatureUpdater()
    start = time.perf_counter()
    count = 0
    for row in df.iter_rows(named=True):
        updater.update(row)
        count += 1
    elapsed = time.perf_counter() - start
    return count, elapsed


def benchmark_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", exists=True, help="输入 Level2 文件"),
    ],
    symbol: Annotated[str | None, typer.Option("--symbol", help="按 symbol 过滤")] = None,
    canonicalize: Annotated[
        bool,
        typer.Option(
            "--canonicalize",
            help="启用字段别名适配（timestamp/code/trade_price 等映射到标准 schema）",
        ),
    ] = False,
    rows: Annotated[int, typer.Option("--rows", min=100)] = 200000,
    mode: Annotated[str, typer.Option("--mode", help="batch|stream|both")] = "both",
) -> None:
    df = read_level2_with_filters(input_path, symbol=symbol, canonicalize=canonicalize).head(rows)

    if mode not in {"batch", "stream", "both"}:
        raise typer.BadParameter("--mode 必须是 batch|stream|both")

    if mode in {"batch", "both"}:
        n, elapsed = _run_batch(df)
        throughput = n / elapsed if elapsed > 0 else 0.0
        typer.echo(f"[batch] rows={n}, elapsed={elapsed:.4f}s, throughput={throughput:.2f} rows/s")

    if mode in {"stream", "both"}:
        n, elapsed = _run_stream(df)
        throughput = n / elapsed if elapsed > 0 else 0.0
        typer.echo(f"[stream] rows={n}, elapsed={elapsed:.4f}s, throughput={throughput:.2f} ev/s")
