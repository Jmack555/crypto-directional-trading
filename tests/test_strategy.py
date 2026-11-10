from datetime import datetime

from crypto_directional.market_data.coinbase import Ticker
from crypto_directional.strategy.momentum import MomentumStrategy


def test_strategy_waits_for_warmup():
    strategy = MomentumStrategy()
    tick = Ticker("BTC-USD", 100, 99.9, 100.1, datetime.utcnow(), 1.0, datetime.utcnow())
    assert strategy.on_ticker(tick) is None
