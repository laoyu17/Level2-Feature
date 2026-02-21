from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from l2_features.cli.main import app


def test_cli_replay_supports_parquet_and_csv_output(sample_csv_path: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    parquet_path = tmp_path / "replay.parquet"
    csv_path = tmp_path / "replay.csv"

    result_parquet = runner.invoke(
        app,
        [
            "replay",
            "--input",
            str(sample_csv_path),
            "--limit",
            "50",
            "--output",
            str(parquet_path),
        ],
    )
    assert result_parquet.exit_code == 0, result_parquet.output
    assert parquet_path.exists()
    assert "trade_sign" in pl.read_parquet(parquet_path).columns

    result_csv = runner.invoke(
        app,
        [
            "replay",
            "--input",
            str(sample_csv_path),
            "--limit",
            "50",
            "--output",
            str(csv_path),
        ],
    )
    assert result_csv.exit_code == 0, result_csv.output
    assert csv_path.exists()
    assert "trade_sign" in pl.read_csv(csv_path).columns


def test_cli_replay_rejects_unsupported_output_suffix(
    sample_csv_path: Path,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    bad_path = tmp_path / "replay.json"
    result = runner.invoke(
        app,
        [
            "replay",
            "--input",
            str(sample_csv_path),
            "--limit",
            "10",
            "--output",
            str(bad_path),
        ],
    )

    assert result.exit_code != 0
    assert "--output 仅支持 .parquet 或 .csv" in result.output
