from crypto_directional.risk import RiskManager
from crypto_directional.strategy.momentum import Signal


def signal():
    return Signal("BTC-USD", "long", 100.0, 99.0, 101.5, 0.7, "test")


def manager():
    return RiskManager(10_000, 0.0025, 3, 0.02, 12)


def test_risk_sizes_position_from_stop_distance():
    result = manager().approve(signal(), 2, 0, 10, 2000)
    assert result.approved
    assert result.quantity == 25


def test_rejects_stale_data():
    result = manager().approve(signal(), 2, 0, 2500, 2000)
    assert not result.approved
    assert result.reason == "stale market data"


def test_rejects_wide_spread():
    result = manager().approve(signal(), 20, 0, 10, 2000)
    assert not result.approved


def test_position_limit():
    result = manager().approve(signal(), 2, 3, 10, 2000)
    assert not result.approved
