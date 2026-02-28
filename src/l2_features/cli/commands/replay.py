from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from l2_features.io.reader import read_level2_with_filters
from l2_features.stream.updater import StreamFeatureUpdater

SUPPORTED_REPLAY_OUTPUT_SUFFIXES = {".parquet", ".csv"}
TS_UNIT_TO_SECONDS_DENOMINATOR = {
    "ns": 1_000_000_000.0,
    "us": 1_000_000.0,
    "ms": 1_000.0,
    "s": 1.0,
}


def _validate_output_path(output_path: Path | None) -> None:
    if output_path is None:
        return

    suffix = output_path.suffix.lower()
    if suffix not in SUPPORTED_REPLAY_OUTPUT_SUFFIXES:
        raise typer.BadParameter("仅支持 .parquet 或 .csv", param_hint="--output")


def replay_command(
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
    speed: Annotated[float, typer.Option("--speed", min=0.1, help="回放倍速")] = 1.0,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="最多回放事件数")] = 2000,
    realtime: Annotated[
        bool,
        typer.Option("--realtime", help="按时间戳模拟实时回放"),
    ] = False,
    ts_unit: Annotated[
        str,
        typer.Option(
            "--ts-unit",
            help="时间戳单位（仅在 --realtime 时生效）：ns/us/ms/s",
            case_sensitive=False,
        ),
    ] = "ns",
    output_path: Annotated[
        Path | None,
        typer.Option("--output", help="将回放结果导出为 parquet/csv"),
    ] = None,
) -> None:
    _validate_output_path(output_path)
    ts_unit_normalized = ts_unit.lower()
    if ts_unit_normalized not in TS_UNIT_TO_SECONDS_DENOMINATOR:
        raise typer.BadParameter(
            "仅支持 ns/us/ms/s",
            param_hint="--ts-unit",
        )

    df = read_level2_with_filters(input_path, symbol=symbol, canonicalize=canonicalize)
    if limit:
        df = df.head(limit)

    updater = StreamFeatureUpdater()
    out_rows: list[dict[str, float | int | str]] = []

    last_ts: int | None = None
    started = time.perf_counter()
    for row in df.iter_rows(named=True):
        ts = int(row["ts"])
        if realtime and last_ts is not None and ts > last_ts:
            wait_seconds = (
                (ts - last_ts) / TS_UNIT_TO_SECONDS_DENOMINATOR[ts_unit_normalized]
            ) / speed
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
        out_df = pl.DataFrame(out_rows)
        suffix = output_path.suffix.lower()
        if suffix == ".parquet":
            out_df.write_parquet(output_path)
        else:
            out_df.write_csv(output_path)
        typer.echo(f"Saved replay features to {output_path.as_posix()}")
