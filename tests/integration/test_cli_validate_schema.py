from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from l2_features.cli.main import app


def test_cli_validate_schema(sample_csv_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["validate-schema", "--input", str(sample_csv_path)])

    assert result.exit_code == 0
    assert "Schema valid" in result.output
