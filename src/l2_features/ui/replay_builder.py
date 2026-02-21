from __future__ import annotations

from typing import Any

import polars as pl

from l2_features.features.engine import compute_features_batch
from l2_features.stream.updater import StreamFeatureUpdater


def normalize_replay_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized in {"batch", "batch-playback"}:
        return "batch-playback"
    if normalized in {"stream", "stream-playback"}:
        return "stream-playback"
    raise ValueError(f"Unsupported replay mode: {mode}")


def build_replay_frames(
    source_frames: list[dict[str, Any]],
    mode: str,
) -> list[dict[str, Any]]:
    if not source_frames:
        return []

    replay_mode = normalize_replay_mode(mode)
    if replay_mode == "batch-playback":
        source_df = pl.DataFrame(source_frames)
        features = compute_features_batch(source_df, keep_raw=True)
        return [row for row in features.iter_rows(named=True)]

    updater = StreamFeatureUpdater()
    replay_frames: list[dict[str, Any]] = []
    for frame in source_frames:
        merged = dict(frame)
        merged.update(updater.update(frame))
        replay_frames.append(merged)
    return replay_frames
