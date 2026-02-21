from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Any

import polars as pl

from l2_features.features.engine import compute_features_batch
from l2_features.io.reader import read_level2_with_filters
from l2_features.stream.updater import StreamFeatureUpdater

try:
    from PyQt6.QtCore import QObject, QTimer, pyqtSignal
except Exception as exc:  # pragma: no cover
    raise RuntimeError("PyQt6 is required for UI components") from exc


class ReplayViewModel(QObject):
    data_loaded = pyqtSignal(int)
    frame_changed = pyqtSignal(dict)
    stats_changed = pyqtSignal(str)
    replay_finished = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._speed = 1.0
        self._interval_ms = 50
        self._mode = "batch-playback"

        self._source_frames: list[dict[str, Any]] = []
        self._frames: list[dict[str, Any]] = []
        self._idx = 0
        self._history: dict[str, deque[float]] = {
            "obi_l1": deque(maxlen=500),
            "spread_abs": deque(maxlen=500),
            "instant_impact": deque(maxlen=500),
        }

    @property
    def history(self) -> dict[str, deque[float]]:
        return self._history

    @property
    def mode(self) -> str:
        return self._mode

    def set_mode(self, mode: str) -> None:
        normalized = mode.strip().lower()
        if normalized in {"batch", "batch-playback"}:
            target = "batch-playback"
        elif normalized in {"stream", "stream-playback"}:
            target = "stream-playback"
        else:
            raise ValueError(f"Unsupported replay mode: {mode}")

        if target == self._mode:
            return

        self._mode = target
        if self._source_frames:
            self._rebuild_frames()
            self._idx = 0
            for values in self._history.values():
                values.clear()
        self.stats_changed.emit(f"Replay mode: {self._mode}")

    def load_file(self, path: Path, symbol: str | None = None, limit: int = 5000) -> None:
        df = read_level2_with_filters(path, symbol=symbol).head(limit)
        self._source_frames = [r for r in df.iter_rows(named=True)]
        self._rebuild_frames()
        self._idx = 0

        for values in self._history.values():
            values.clear()
        self.data_loaded.emit(len(self._frames))
        self.stats_changed.emit(f"Loaded {len(self._frames)} frames ({self._mode})")

    def _rebuild_frames(self) -> None:
        if not self._source_frames:
            self._frames = []
            return

        if self._mode == "batch-playback":
            source_df = pl.DataFrame(self._source_frames)
            features = compute_features_batch(source_df, keep_raw=True)
            self._frames = [r for r in features.iter_rows(named=True)]
            return

        updater = StreamFeatureUpdater()
        replay_frames: list[dict[str, Any]] = []
        for frame in self._source_frames:
            merged = dict(frame)
            merged.update(updater.update(frame))
            replay_frames.append(merged)
        self._frames = replay_frames

    def set_speed(self, speed: float) -> None:
        self._speed = max(speed, 0.1)
        self._timer.setInterval(max(int(self._interval_ms / self._speed), 1))

    def play(self) -> None:
        if not self._frames:
            self.stats_changed.emit("No data loaded")
            return
        self._timer.start(max(int(self._interval_ms / self._speed), 1))

    def pause(self) -> None:
        self._timer.stop()

    def stop(self) -> None:
        self.pause()
        self._idx = 0

    def _on_tick(self) -> None:
        if self._idx >= len(self._frames):
            self._timer.stop()
            self.replay_finished.emit()
            return

        frame = self._frames[self._idx]
        self._idx += 1

        for key in self._history:
            self._history[key].append(float(frame.get(key, 0.0)))

        self.frame_changed.emit(frame)
        self.stats_changed.emit(f"Frame {self._idx}/{len(self._frames)}")
