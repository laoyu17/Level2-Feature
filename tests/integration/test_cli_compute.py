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
