from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from l2_features.io.reader import read_level2
from l2_features.schema import detect_depth_levels, validate_required_columns


def validate_schema_command(
    input_path: Annotated[
        Path,
        typer.Option("--input", exists=True, help="输入 Level2 文件"),
    ],
) -> None:
    df = read_level2(input_path, lazy=False)
    validate_required_columns(df)
    depth = detect_depth_levels(df.columns)
    typer.echo(f"Schema valid. rows={df.height}, cols={df.width}, depth={depth}")
