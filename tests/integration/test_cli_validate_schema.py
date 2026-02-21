from __future__ import annotations

from pathlib import Path

import polars as pl
from typer.testing import CliRunner

from l2_features.cli.main import app


def test_cli_validate_schema(sample_csv_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["validate-schema", "--input", str(sample_csv_path)])

    assert result.exit_code == 0
    assert "Schema valid" in result.output


def test_cli_validate_schema_rejects_incomplete_depth(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad_depth.csv"
    pl.DataFrame(
        {
            "ts": [1],
            "symbol": ["000001.SZ"],
            "event_type": ["quote"],
            "last_px": [10.0],
            "last_sz": [100.0],
            "bid_px_1": [9.99],
            "bid_sz_1": [2000.0],
            "ask_px_1": [10.01],
            "ask_sz_1": [2100.0],
            "bid_px_2": [9.98],
            "ask_px_2": [10.02],
        }
    ).write_csv(bad_path)

    runner = CliRunner()
    result = runner.invoke(app, ["validate-schema", "--input", str(bad_path)])

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Incomplete depth columns" in str(result.exception)


def test_cli_validate_schema_with_canonicalize_aliases(tmp_path: Path) -> None:
    alias_path = tmp_path / "alias_depth.csv"
    pl.DataFrame(
        {
            "timestamp": [1],
            "code": ["000001.SZ"],
            "type": ["quote"],
            "trade_price": [10.0],
            "trade_size": [100.0],
            "bid_px_1": [9.99],
            "bid_sz_1": [2000.0],
            "ask_px_1": [10.01],
            "ask_sz_1": [2100.0],
        }
    ).write_csv(alias_path)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["validate-schema", "--input", str(alias_path), "--canonicalize"],
    )

    assert result.exit_code == 0
    assert "Schema valid" in result.output
