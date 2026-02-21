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
from l2_features.trade_sign import parse_trade_side_value


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
    return std * (n**0.5)


def _safe_div(num: float, den: float, default: float = 0.0) -> float:
    return num / den if abs(den) > 1e-12 else default


def _detect_depth_levels(event: Mapping[str, Any]) -> int:
    depth = 0
    for i in range(1, 11):
        keys = (f"bid_px_{i}", f"bid_sz_{i}", f"ask_px_{i}", f"ask_sz_{i}")
        if all(k in event for k in keys):
            depth = i
        else:
            break
    return max(depth, 1)


def _depth_sum(event: Mapping[str, Any], prefix: str, depth_levels: int) -> float:
    total = 0.0
    for i in range(1, depth_levels + 1):
        total += float(event.get(f"{prefix}_{i}", 0.0))
    return total


def _depth_weighted_price_distance(event: Mapping[str, Any], side: str, depth_levels: int) -> float:
    if side == "ask":
        top_px = float(event["ask_px_1"])
        total_sz = 0.0
        weighted_distance = 0.0
        for i in range(1, depth_levels + 1):
            px = float(event.get(f"ask_px_{i}", top_px))
            sz = float(event.get(f"ask_sz_{i}", 0.0))
            weighted_distance += (px - top_px) * sz
            total_sz += sz
    else:
        top_px = float(event["bid_px_1"])
        total_sz = 0.0
        weighted_distance = 0.0
        for i in range(1, depth_levels + 1):
            px = float(event.get(f"bid_px_{i}", top_px))
            sz = float(event.get(f"bid_sz_{i}", 0.0))
            weighted_distance += (top_px - px) * sz
            total_sz += sz

    return _safe_div(weighted_distance, total_sz)


def _scaled_std_last(values: list[float], window: int) -> float:
    # batch 模式中首条 log_return 为 null，因此流式对齐时需要多一条样本后再计算窗口波动
    if len(values) <= window:
        return 0.0
    return float(_scaled_std(np.array(values[-window:], dtype=np.float64)))


def _rolling_mean_last(values: list[float], window: int) -> float:
    if len(values) < window:
        return 0.0
    return float(sum(values[-window:]) / window)


class StreamFeatureUpdater:
    """在线增量计算器，适用于逐条 Tick/Level2 事件。"""

    def __init__(
        self,
        *,
        rv_window: int = 100,
        rv_windows: tuple[int, ...] = (20, 100, 500),
        sign_window: int = 20,
    ) -> None:
        normalized_windows = tuple(sorted({w for w in rv_windows if w >= 2}))
        if not normalized_windows:
            raise ValueError("rv_windows must contain at least one value >= 2")

        self._states: dict[str, StreamState] = {}
        self._legacy_rv_window = max(rv_window, 2)
        self._rv_windows = normalized_windows
        self._sign_window = max(sign_window, 1)
        self._max_return_window = max(max(self._rv_windows), self._legacy_rv_window)

    def _state(self, symbol: str) -> StreamState:
        if symbol not in self._states:
            self._states[symbol] = StreamState(
                symbol=symbol,
                rv_window=self._max_return_window,
                sign_window=self._sign_window,
            )
        return self._states[symbol]

    def update(self, event: Mapping[str, Any]) -> dict[str, float | int | str]:
        symbol = str(event["symbol"])
        state = self._state(symbol)

        ts = int(event["ts"])
        event_type = str(event.get("event_type", ""))
        bid_px = float(event["bid_px_1"])
        ask_px = float(event["ask_px_1"])
        bid_sz = float(event["bid_sz_1"])
        ask_sz = float(event["ask_sz_1"])
        last_px = float(event.get("last_px", 0.0))
        last_sz = float(event.get("last_sz", 0.0))

        depth_levels = _detect_depth_levels(event)
        levels_5 = min(depth_levels, 5)
        levels_10 = min(depth_levels, 10)

        bid_depth_5 = _depth_sum(event, "bid_sz", levels_5)
        ask_depth_5 = _depth_sum(event, "ask_sz", levels_5)
        bid_depth_10 = _depth_sum(event, "bid_sz", levels_10)
        ask_depth_10 = _depth_sum(event, "ask_sz", levels_10)

        spread_abs = ask_px - bid_px
        spread_bps = _safe_div(spread_abs, bid_px)
        mid_px = (ask_px + bid_px) * 0.5
        depth_sum = bid_sz + ask_sz
        obi_l1 = _safe_div(bid_sz - ask_sz, depth_sum)
        obi_l5 = _safe_div(bid_depth_5 - ask_depth_5, bid_depth_5 + ask_depth_5)
        obi_l10 = _safe_div(bid_depth_10 - ask_depth_10, bid_depth_10 + ask_depth_10)
        depth_ratio_l10 = _safe_div(bid_depth_10, ask_depth_10)
        microprice = _safe_div(ask_px * bid_sz + bid_px * ask_sz, depth_sum, default=mid_px)
        ask_slope = _depth_weighted_price_distance(event, "ask", levels_10)
        bid_slope = _depth_weighted_price_distance(event, "bid", levels_10)
        book_slope = ask_slope + bid_slope

        order_flow_imbalance = 0.0
        cancel_intensity = 0.0
        add_cancel_ratio = 0.0
        bid_cancel = 0.0
        ask_cancel = 0.0
        if state.last_bid_px is not None and state.last_ask_px is not None:
            prev_bid_px = state.last_bid_px
            prev_ask_px = state.last_ask_px
            prev_bid_sz = state.last_bid_sz or 0.0
            prev_ask_sz = state.last_ask_sz or 0.0

            bid_in = bid_sz if bid_px >= prev_bid_px else 0.0
            bid_out = prev_bid_sz if bid_px <= prev_bid_px else 0.0
            ask_in = ask_sz if ask_px <= prev_ask_px else 0.0
            ask_out = prev_ask_sz if ask_px >= prev_ask_px else 0.0
            order_flow_imbalance = bid_in - bid_out - ask_in + ask_out

            bid_add = max(bid_sz - prev_bid_sz, 0.0)
            ask_add = max(ask_sz - prev_ask_sz, 0.0)
            bid_cancel = max(prev_bid_sz - bid_sz, 0.0)
            ask_cancel = max(prev_ask_sz - ask_sz, 0.0)

            cancel_total = bid_cancel + ask_cancel
            add_total = bid_add + ask_add
            prev_depth = prev_bid_sz + prev_ask_sz

            cancel_intensity = _safe_div(cancel_total, prev_depth)
            add_cancel_ratio = _safe_div(add_total, cancel_total)

        trade_sign = parse_trade_side_value(event.get("side"))
        if trade_sign is None and state.last_trade_px is not None:
            if last_px > state.last_trade_px:
                trade_sign = 1.0
            elif last_px < state.last_trade_px:
                trade_sign = -1.0
            else:
                trade_sign = 0.0
        elif trade_sign is None:
            trade_sign = 0.0

        state.push_trade_sign(trade_sign)
        sign_values = list(state.trade_signs)
        trade_sign_imbalance_20 = _rolling_mean_last(sign_values, self._sign_window)

        signed_turnover = trade_sign * last_px * last_sz
        turnover = last_px * last_sz

        instant_impact = _safe_div(abs(last_px - mid_px), mid_px)

        log_return = 0.0
        if state.last_trade_px is not None and state.last_trade_px > 0 and last_px > 0:
            log_return = log(last_px / state.last_trade_px)
        amihud_proxy = _safe_div(abs(log_return), last_sz + 1e-9)

        state.push_return(log_return)
        return_values = list(state.returns)
        rv_values = {f"rv_{w}": _scaled_std_last(return_values, w) for w in self._rv_windows}

        legacy_window = min(len(return_values), self._legacy_rv_window)
        rv_stream = 0.0
        if legacy_window >= 2:
            rv_stream = float(
                _scaled_std(np.array(return_values[-legacy_window:], dtype=np.float64))
            )

        state.last_bid_px = bid_px
        state.last_ask_px = ask_px
        state.last_bid_sz = bid_sz
        state.last_ask_sz = ask_sz
        state.last_trade_px = last_px

        output: dict[str, float | int | str] = {
            "ts": ts,
            "symbol": symbol,
            "event_type": event_type,
            "mid_px": mid_px,
            "spread_abs": spread_abs,
            "spread_bps": spread_bps,
            "obi_l1": obi_l1,
            "obi_l5": obi_l5,
            "obi_l10": obi_l10,
            "depth_ratio_l10": depth_ratio_l10,
            "microprice": microprice,
            "ask_slope": ask_slope,
            "bid_slope": bid_slope,
            "book_slope": book_slope,
            "bid_depth_l10": bid_depth_10,
            "ask_depth_l10": ask_depth_10,
            "order_flow_imbalance": order_flow_imbalance,
            "cancel_intensity": cancel_intensity,
            "add_cancel_ratio": add_cancel_ratio,
            "bid_cancel": bid_cancel,
            "ask_cancel": ask_cancel,
            "trade_sign": trade_sign,
            "trade_sign_imbalance_20": trade_sign_imbalance_20,
            "signed_turnover": signed_turnover,
            "turnover": turnover,
            "instant_impact": instant_impact,
            "amihud_proxy": amihud_proxy,
            "log_return": log_return,
            "rv_stream": rv_stream,
        }
        output.update(rv_values)
        return output

    def update_many(
        self,
        events: Iterable[Mapping[str, Any]],
    ) -> Iterator[dict[str, float | int | str]]:
        for event in events:
            yield self.update(event)
