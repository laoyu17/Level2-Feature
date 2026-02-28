from __future__ import annotations

import re
from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from l2_features.cli.main import app

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def _write_minimal_replay_csv(path: Path, ts_values: list[int]) -> None:
    rows = [
        {
            "ts": ts,
            "symbol": "000001.SZ",
            "bid_px_1": 9.99,
            "bid_sz_1": 2000,
            "ask_px_1": 10.01,
            "ask_sz_1": 1800,
            "last_px": 10.0,
            "last_sz": 100.0,
            "event_type": "trade",
        }
        for ts in ts_values
    ]
    pl.DataFrame(rows).write_csv(path)


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
    assert "Replay done:" not in result.stdout
    assert not bad_path.exists()

    error_text = result.stderr or result.output
    plain_error = ANSI_ESCAPE_RE.sub("", error_text)
    assert "仅支持 .parquet 或 .csv" in plain_error


def test_cli_replay_rejects_invalid_ts_unit(sample_csv_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "replay",
            "--input",
            str(sample_csv_path),
            "--limit",
            "2",
            "--realtime",
            "--ts-unit",
            "minute",
        ],
    )

    assert result.exit_code != 0
    assert "Replay done:" not in result.stdout

    error_text = result.stderr or result.output
    plain_error = ANSI_ESCAPE_RE.sub("", error_text)
    assert "仅支持 ns/us/ms/s" in plain_error


def test_cli_replay_realtime_ts_unit_controls_wait_duration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = CliRunner()
    sleep_calls: list[float] = []
    monkeypatch.setattr(
        "l2_features.cli.commands.replay.time.sleep",
        lambda seconds: sleep_calls.append(seconds),
    )

    for ts_unit, ts_values in (
        ("ns", [1_000_000_000, 1_500_000_000]),
        ("us", [1_000_000, 1_500_000]),
        ("ms", [1_000, 1_500]),
    ):
        input_path = tmp_path / f"replay_{ts_unit}.csv"
        _write_minimal_replay_csv(input_path, ts_values)
        start_len = len(sleep_calls)

        result = runner.invoke(
            app,
            [
                "replay",
                "--input",
                str(input_path),
                "--limit",
                "2",
                "--realtime",
                "--ts-unit",
                ts_unit,
                "--speed",
                "1.0",
            ],
        )
        assert result.exit_code == 0, result.output
        assert len(sleep_calls) == start_len + 1
        assert sleep_calls[-1] == pytest.approx(0.5)
