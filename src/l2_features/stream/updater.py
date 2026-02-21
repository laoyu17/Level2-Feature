from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from math import log
from typing import Any

import numpy as np

try:
    from numba import njit
except Exception:  # pragma: no cover - fallback for unsupported python/arch
    def njit(*_args: Any, **_kwargs: Any):  # type: ignore[misc]
        def decorator(func: Any) -> Any:
            return func

        return decorator

from l2_features.stream.state import StreamState


@njit(cache=True)
def _scaled_std(values: np.ndarray) -> float:
    n = values.size
    if n < 2:
        return 0.0

    total = 0.0
    for i in range(n):
        total += values[i]
    mean = total / n

    var_sum = 0.0
    for i in range(n):
        diff = values[i] - mean
        var_sum += diff * diff

    std = (var_sum / (n - 1)) ** 0.5
    return std * (n ** 0.5)


class StreamFeatureUpdater:
    """在线增量计算器，适用于逐条 Tick/Level2 事件。"""

    def __init__(self, *, rv_window: int = 100) -> None:
        self._states: dict[str, StreamState] = {}
        self._rv_window = rv_window

    def _state(self, symbol: str) -> StreamState:
        if symbol not in self._states:
            self._states[symbol] = StreamState(symbol=symbol, rv_window=self._rv_window)
        return self._states[symbol]

    def update(self, event: Mapping[str, Any]) -> dict[str, float | int | str]:
        symbol = str(event["symbol"])
        state = self._state(symbol)

        ts = int(event["ts"])
        bid_px = float(event["bid_px_1"])
        ask_px = float(event["ask_px_1"])
        bid_sz = float(event["bid_sz_1"])
        ask_sz = float(event["ask_sz_1"])
        last_px = float(event.get("last_px", 0.0))

        spread_abs = ask_px - bid_px
        mid_px = (ask_px + bid_px) * 0.5
        depth_sum = bid_sz + ask_sz
        obi_l1 = (bid_sz - ask_sz) / depth_sum if depth_sum > 0 else 0.0
        microprice = (ask_px * bid_sz + bid_px * ask_sz) / depth_sum if depth_sum > 0 else mid_px

        order_flow_imbalance = 0.0
        cancel_intensity = 0.0
        if state.last_bid_px is not None and state.last_ask_px is not None:
            bid_in = bid_sz if bid_px >= state.last_bid_px else 0.0
            bid_out = (
                state.last_bid_sz
                if bid_px <= state.last_bid_px and state.last_bid_sz
                else 0.0
            )
            ask_in = ask_sz if ask_px <= state.last_ask_px else 0.0
            ask_out = (
                state.last_ask_sz
                if ask_px >= state.last_ask_px and state.last_ask_sz
                else 0.0
            )
            order_flow_imbalance = bid_in - bid_out - ask_in + ask_out

            bid_cancel = max((state.last_bid_sz or 0.0) - bid_sz, 0.0)
            ask_cancel = max((state.last_ask_sz or 0.0) - ask_sz, 0.0)
            prev_depth = (state.last_bid_sz or 0.0) + (state.last_ask_sz or 0.0)
            cancel_intensity = (bid_cancel + ask_cancel) / prev_depth if prev_depth > 0 else 0.0

        instant_impact = abs(last_px - mid_px) / mid_px if mid_px > 0 else 0.0

        log_return = 0.0
        if state.last_trade_px and state.last_trade_px > 0 and last_px > 0:
            log_return = log(last_px / state.last_trade_px)

        state.push_return(log_return)
        rv_window = _scaled_std(np.array(list(state.returns), dtype=np.float64))

        state.last_bid_px = bid_px
        state.last_ask_px = ask_px
        state.last_bid_sz = bid_sz
        state.last_ask_sz = ask_sz
        state.last_trade_px = last_px

        return {
            "ts": ts,
            "symbol": symbol,
            "mid_px": mid_px,
            "spread_abs": spread_abs,
            "obi_l1": obi_l1,
            "microprice": microprice,
            "order_flow_imbalance": order_flow_imbalance,
            "cancel_intensity": cancel_intensity,
            "instant_impact": instant_impact,
            "log_return": log_return,
            "rv_stream": rv_window,
        }

    def update_many(
        self,
        events: Iterable[Mapping[str, Any]],
    ) -> Iterator[dict[str, float | int | str]]:
        for event in events:
            yield self.update(event)
