from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from l2_features.features.engine import compute_features_batch
from l2_features.io.reader import read_level2_with_filters
from l2_features.schema import detect_depth_levels


def compute_entry(
    input_path: Annotated[
        Path,
        typer.Option("--input", exists=True, help="输入 Level2 文件(csv/parquet)"),
    ],
    output_path: Annotated[
        Path,
        typer.Option("--output", help="输出文件(parquet/csv/txt)"),
    ],
    symbol: Annotated[str | None, typer.Option("--symbol", help="按 symbol 过滤")] = None,
    canonicalize: Annotated[
        bool,
        typer.Option(
            "--canonicalize",
            help="启用字段别名适配（timestamp/code/trade_price 等映射到标准 schema）",
        ),
    ] = False,
    depth_levels: Annotated[int, typer.Option("--depth-levels", min=1, max=10)] = 10,
    strict_depth: Annotated[
        bool,
        typer.Option(
            "--strict-depth",
            help="若请求深度大于数据深度则报错；默认关闭并自动降级到可用深度",
        ),
    ] = False,
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

    df = read_level2_with_filters(input_path, symbol=symbol, canonicalize=canonicalize)
    detected_depth = detect_depth_levels(df.columns)
    effective_depth = min(depth_levels, detected_depth)
    selected = [f.strip() for f in features.split(",")] if features else None

    feature_df = compute_features_batch(
        df,
        depth_levels=depth_levels,
        selected_features=selected,
        keep_raw=keep_raw,
        strict_depth=strict_depth,
    )

    suffix = output_path.suffix.lower()
    if suffix == ".parquet":
        feature_df.write_parquet(output_path)
    elif suffix in {".csv", ".txt"}:
        feature_df.write_csv(output_path)
    else:
        raise typer.BadParameter("--output 仅支持 .parquet/.csv/.txt")

    depth_note = (
        f"depth(requested={depth_levels}, detected={detected_depth}, "
        f"effective={effective_depth})"
    )
    typer.echo(
        f"Done: rows={feature_df.height}, cols={feature_df.width}, {depth_note}, "
        f"output={output_path.as_posix()}"
    )
