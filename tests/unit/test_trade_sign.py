from __future__ import annotations

from l2_features.trade_sign import parse_trade_side_value


def test_parse_trade_side_value_tokens() -> None:
    assert parse_trade_side_value("B") == 1.0
    assert parse_trade_side_value("buy") == 1.0
    assert parse_trade_side_value("S") == -1.0
    assert parse_trade_side_value("SELL") == -1.0
    assert parse_trade_side_value("0") == 0.0
    assert parse_trade_side_value("UNKNOWN") is None


def test_parse_trade_side_value_numeric() -> None:
    assert parse_trade_side_value(1) == 1.0
    assert parse_trade_side_value(-1) == -1.0
    assert parse_trade_side_value(0) == 0.0
    assert parse_trade_side_value(2) is None
