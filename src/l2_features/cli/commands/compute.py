from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from l2_features.features.engine import compute_features_batch
from l2_features.io.reader import read_level2_with_filters


def compute_entry(
    input_path: Annotated[
        Path,
        typer.Option("--input", exists=True, help="输入 Level2 文件(csv/parquet)"),
    ],
    output_path: Annotated[
        Path,
        typer.Option("--output", help="输出文件(parquet/csv)"),
    ],
    symbol: Annotated[str | None, typer.Option("--symbol", help="按 symbol 过滤")] = None,
    depth_levels: Annotated[int, typer.Option("--depth-levels", min=1, max=10)] = 10,
    features: Annotated[
        str | None,
        typer.Option("--features", help="逗号分隔的特征列名"),
    ] = None,
    keep_raw: Annotated[
        bool,
        typer.Option("--keep-raw", help="输出是否保留原始列"),
    ] = False,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = read_level2_with_filters(input_path, symbol=symbol)
    selected = [f.strip() for f in features.split(",")] if features else None

    feature_df = compute_features_batch(
        df,
        depth_levels=depth_levels,
        selected_features=selected,
        keep_raw=keep_raw,
    )

    suffix = output_path.suffix.lower()
    if suffix == ".parquet":
        feature_df.write_parquet(output_path)
    elif suffix in {".csv", ".txt"}:
        feature_df.write_csv(output_path)
    else:
        raise typer.BadParameter("--output 仅支持 .parquet 或 .csv")

    typer.echo(
        f"Done: rows={feature_df.height}, cols={feature_df.width}, output={output_path.as_posix()}"
    )
