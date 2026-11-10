from datetime import UTC, datetime

from crypto_directional.market_data.coinbase import Ticker
from crypto_directional.strategy.momentum import MomentumStrategy


def test_strategy_waits_for_warmup():
    strategy = MomentumStrategy()
    now = datetime.now(UTC)
    tick = Ticker("BTC-USD", 100, 99.9, 100.1, now, 1.0, now)
    assert strategy.on_ticker(tick) is None
