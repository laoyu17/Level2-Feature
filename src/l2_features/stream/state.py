from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass(slots=True)
class StreamState:
    """单个 symbol 的流式特征状态。"""

    symbol: str
    rv_window: int = 500
    sign_window: int = 20
    last_bid_px: float | None = None
    last_ask_px: float | None = None
    last_bid_sz: float | None = None
    last_ask_sz: float | None = None
    last_trade_px: float | None = None
    returns: deque[float] = field(default_factory=deque)
    trade_signs: deque[float] = field(default_factory=deque)

    def push_return(self, value: float) -> None:
        self.returns.append(value)
        while len(self.returns) > self.rv_window:
            self.returns.popleft()

    def push_trade_sign(self, value: float) -> None:
        self.trade_signs.append(value)
        while len(self.trade_signs) > self.sign_window:
            self.trade_signs.popleft()
