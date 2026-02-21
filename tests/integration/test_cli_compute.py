from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from l2_features.cli.main import app


def test_cli_compute(sample_csv_path: Path, tmp_path: Path) -> None:
    runner = CliRunner()
    out_path = tmp_path / "features.parquet"

    result = runner.invoke(
        app,
        [
            "compute",
            "--input",
            str(sample_csv_path),
            "--output",
            str(out_path),
            "--depth-levels",
            "10",
        ],
    )

    assert result.exit_code == 0, result.output
    assert out_path.exists()

    df = pl.read_parquet(out_path)
    assert df.height > 0
    assert "obi_l1" in df.columns


def test_cli_compute_strict_depth_rejects_shallow_data(tmp_path: Path) -> None:
    input_path = tmp_path / "l1.csv"
    out_path = tmp_path / "features.parquet"
    pl.DataFrame(
        {
            "ts": [1, 2],
            "symbol": ["000001.SZ", "000001.SZ"],
            "event_type": ["quote", "quote"],
            "last_px": [10.0, 10.01],
            "last_sz": [100.0, 100.0],
            "bid_px_1": [9.99, 10.0],
            "bid_sz_1": [1000.0, 1100.0],
            "ask_px_1": [10.01, 10.02],
            "ask_sz_1": [1200.0, 1300.0],
        }
    ).write_csv(input_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compute",
            "--input",
            str(input_path),
            "--output",
            str(out_path),
            "--depth-levels",
            "10",
            "--strict-depth",
        ],
    )

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Requested depth_levels=10 exceeds detected depth=1" in str(result.exception)


def test_cli_compute_with_canonicalize_aliases(tmp_path: Path) -> None:
    input_path = tmp_path / "alias_input.csv"
    out_path = tmp_path / "features.parquet"
    pl.DataFrame(
        {
            "timestamp": [1, 2],
            "code": ["000001.SZ", "000001.SZ"],
            "type": ["quote", "quote"],
            "trade_price": [10.0, 10.01],
            "trade_size": [100.0, 100.0],
            "bid_px_1": [9.99, 10.0],
            "bid_sz_1": [1000.0, 1100.0],
            "ask_px_1": [10.01, 10.02],
            "ask_sz_1": [1200.0, 1300.0],
        }
    ).write_csv(input_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "compute",
            "--input",
            str(input_path),
            "--output",
            str(out_path),
            "--canonicalize",
        ],
    )

    assert result.exit_code == 0, result.output
    assert out_path.exists()
    df = pl.read_parquet(out_path)
    assert df.height == 2
    assert "spread_abs" in df.columns
