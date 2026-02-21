from __future__ import annotations

from l2_features.stream.updater import StreamFeatureUpdater


def test_stream_updater_basic() -> None:
    updater = StreamFeatureUpdater(rv_window=10)

    event1 = {
        "ts": 1,
        "symbol": "000001.SZ",
        "bid_px_1": 9.99,
        "ask_px_1": 10.01,
        "bid_sz_1": 2000,
        "ask_sz_1": 1800,
        "last_px": 10.0,
    }
    event2 = {
        "ts": 2,
        "symbol": "000001.SZ",
        "bid_px_1": 10.00,
        "ask_px_1": 10.02,
        "bid_sz_1": 2100,
        "ask_sz_1": 1700,
        "last_px": 10.01,
    }

    out1 = updater.update(event1)
    out2 = updater.update(event2)

    assert out1["symbol"] == "000001.SZ"
    assert "obi_l1" in out1
    assert out2["rv_stream"] >= 0
    assert out2["order_flow_imbalance"] != 0
