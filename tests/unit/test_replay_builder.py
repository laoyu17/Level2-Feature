from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from l2_features.ui.replay_builder import build_replay_frames, normalize_replay_mode


def _sample_frames(sample_csv_path: Path, rows: int = 50) -> list[dict]:
    df = pl.read_csv(sample_csv_path).head(rows)
    return [row for row in df.iter_rows(named=True)]


def test_normalize_replay_mode_aliases() -> None:
    assert normalize_replay_mode("batch") == "batch-playback"
    assert normalize_replay_mode("batch-playback") == "batch-playback"
    assert normalize_replay_mode("stream") == "stream-playback"
    assert normalize_replay_mode("stream-playback") == "stream-playback"


def test_normalize_replay_mode_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="Unsupported replay mode"):
        normalize_replay_mode("realtime")


def test_build_replay_frames_batch_mode(sample_csv_path: Path) -> None:
    frames = _sample_frames(sample_csv_path)
    replay_frames = build_replay_frames(frames, "batch-playback")

    assert len(replay_frames) == len(frames)
    assert "obi_l1" in replay_frames[0]
    assert "rv_20" in replay_frames[-1]


def test_build_replay_frames_stream_mode(sample_csv_path: Path) -> None:
    frames = _sample_frames(sample_csv_path)
    replay_frames = build_replay_frames(frames, "stream-playback")

    assert len(replay_frames) == len(frames)
    assert "obi_l1" in replay_frames[0]
    assert "rv_stream" in replay_frames[-1]
