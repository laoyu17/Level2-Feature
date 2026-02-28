from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import polars as pl
import pytest


class _DummySignalInstance:
    def __init__(self) -> None:
        self.emitted: list[tuple[object, ...]] = []
        self._callbacks: list[object] = []

    def emit(self, *args: object) -> None:
        self.emitted.append(args)
        for callback in self._callbacks:
            callback(*args)

    def connect(self, callback: object) -> None:
        self._callbacks.append(callback)


class _DummySignalDescriptor:
    def __set_name__(self, owner: type[object], name: str) -> None:
        self._name = name

    def __get__(self, instance: object, owner: type[object]) -> object:
        if instance is None:
            return self
        store = instance.__dict__.setdefault("_dummy_signals", {})
        if self._name not in store:
            store[self._name] = _DummySignalInstance()
        return store[self._name]


class _DummyQObject:
    def __init__(self, parent: object | None = None) -> None:
        self._parent = parent


class _DummyTimer:
    def __init__(self, parent: object | None = None) -> None:
        self._parent = parent
        self.timeout = _DummySignalInstance()
        self.running = False
        self.interval_ms = 0

    def setInterval(self, interval_ms: int) -> None:
        self.interval_ms = interval_ms

    def start(self, interval_ms: int) -> None:
        self.interval_ms = interval_ms
        self.running = True

    def stop(self) -> None:
        self.running = False


@pytest.fixture
def replay_viewmodel_module(monkeypatch: pytest.MonkeyPatch):
    qtcore = types.ModuleType("PyQt6.QtCore")
    qtcore.QObject = _DummyQObject
    qtcore.QTimer = _DummyTimer
    qtcore.pyqtSignal = lambda *_args, **_kwargs: _DummySignalDescriptor()

    pyqt6 = types.ModuleType("PyQt6")
    pyqt6.QtCore = qtcore

    monkeypatch.setitem(sys.modules, "PyQt6", pyqt6)
    monkeypatch.setitem(sys.modules, "PyQt6.QtCore", qtcore)
    sys.modules.pop("l2_features.ui.viewmodels.replay_viewmodel", None)

    module = importlib.import_module("l2_features.ui.viewmodels.replay_viewmodel")
    return importlib.reload(module)


def test_replay_viewmodel_load_file_rebuilds_and_emits(
    replay_viewmodel_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vm = replay_viewmodel_module.ReplayViewModel()

    raw_rows = [
        {
            "ts": 1,
            "symbol": "000001.SZ",
            "bid_px_1": 9.99,
            "bid_sz_1": 2000,
            "ask_px_1": 10.01,
            "ask_sz_1": 1800,
            "last_px": 10.0,
            "last_sz": 100.0,
            "event_type": "trade",
        },
        {
            "ts": 2,
            "symbol": "000001.SZ",
            "bid_px_1": 10.0,
            "bid_sz_1": 2100,
            "ask_px_1": 10.02,
            "ask_sz_1": 1700,
            "last_px": 10.01,
            "last_sz": 120.0,
            "event_type": "trade",
        },
    ]
    monkeypatch.setattr(
        replay_viewmodel_module,
        "read_level2_with_filters",
        lambda *_args, **_kwargs: pl.DataFrame(raw_rows),
    )
    monkeypatch.setattr(
        replay_viewmodel_module,
        "build_replay_frames",
        lambda *_args, **_kwargs: [
            {"obi_l1": 0.1, "spread_abs": 0.02, "instant_impact": 0.0},
            {"obi_l1": 0.2, "spread_abs": 0.03, "instant_impact": 0.01},
        ],
    )

    vm.history["obi_l1"].append(1.0)
    vm.history["spread_abs"].append(1.0)
    vm.history["instant_impact"].append(1.0)

    vm.load_file(Path("dummy.csv"), limit=2)

    assert vm._idx == 0
    assert len(vm.history["obi_l1"]) == 0
    assert len(vm.history["spread_abs"]) == 0
    assert len(vm.history["instant_impact"]) == 0
    assert vm.data_loaded.emitted[-1] == (2,)
    assert vm.stats_changed.emitted[-1] == ("Loaded 2 frames (batch-playback)",)


def test_replay_viewmodel_set_mode_resets_state(
    replay_viewmodel_module,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vm = replay_viewmodel_module.ReplayViewModel()
    vm._source_frames = [{"ts": 1}, {"ts": 2}]
    vm._idx = 1
    vm.history["obi_l1"].append(1.0)

    monkeypatch.setattr(
        replay_viewmodel_module,
        "build_replay_frames",
        lambda *_args, **_kwargs: [{"obi_l1": 0.0, "spread_abs": 0.0, "instant_impact": 0.0}],
    )

    vm.set_mode("stream")

    assert vm.mode == "stream-playback"
    assert vm._idx == 0
    assert len(vm.history["obi_l1"]) == 0
    assert vm.stats_changed.emitted[-1] == ("Replay mode: stream-playback",)


def test_replay_viewmodel_tick_updates_history_and_finishes(replay_viewmodel_module) -> None:
    vm = replay_viewmodel_module.ReplayViewModel()
    vm._frames = [
        {"obi_l1": 0.1, "spread_abs": 0.02, "instant_impact": 0.0},
        {"obi_l1": 0.3, "spread_abs": 0.04, "instant_impact": 0.02},
    ]

    vm._on_tick()
    assert vm._idx == 1
    assert vm.history["obi_l1"][-1] == 0.1
    assert vm.stats_changed.emitted[-1] == ("Frame 1/2",)

    vm._on_tick()
    assert vm._idx == 2
    assert vm.history["obi_l1"][-1] == 0.3
    assert vm.stats_changed.emitted[-1] == ("Frame 2/2",)

    vm._on_tick()
    assert vm.replay_finished.emitted[-1] == ()
    assert vm._timer.running is False
