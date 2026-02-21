from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from l2_features.io.reader import read_level2_with_filters
from l2_features.stream.updater import StreamFeatureUpdater


def replay_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", exists=True, help="输入 Level2 文件"),
    ],
    symbol: Annotated[str | None, typer.Option("--symbol", help="按 symbol 过滤")] = None,
    speed: Annotated[float, typer.Option("--speed", min=0.1, help="回放倍速")] = 1.0,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="最多回放事件数")] = 2000,
    realtime: Annotated[
        bool,
        typer.Option("--realtime", help="按时间戳模拟实时回放"),
    ] = False,
    output_path: Annotated[
        Path | None,
        typer.Option("--output", help="将回放结果导出为 parquet"),
    ] = None,
) -> None:
    df = read_level2_with_filters(input_path, symbol=symbol)
    if limit:
        df = df.head(limit)

    updater = StreamFeatureUpdater()
    out_rows: list[dict[str, float | int | str]] = []

    last_ts: int | None = None
    started = time.perf_counter()
    for row in df.iter_rows(named=True):
        ts = int(row["ts"])
        if realtime and last_ts is not None and ts > last_ts:
            wait_seconds = ((ts - last_ts) / 1_000_000_000) / speed
            if wait_seconds > 0:
                time.sleep(min(wait_seconds, 1.0))

        result = updater.update(row)
        out_rows.append(result)
        last_ts = ts

    elapsed = time.perf_counter() - started
    throughput = len(out_rows) / elapsed if elapsed > 0 else 0.0

    typer.echo(
        f"Replay done: rows={len(out_rows)}, elapsed={elapsed:.4f}s, "
        f"throughput={throughput:.2f} ev/s"
    )

    if output_path and out_rows:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pl.DataFrame(out_rows).write_parquet(output_path)
        typer.echo(f"Saved replay features to {output_path.as_posix()}")
