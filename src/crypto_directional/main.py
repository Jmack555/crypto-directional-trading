from __future__ import annotations

import asyncio
import logging

from crypto_directional.config import Settings
from crypto_directional.market_data.coinbase import CoinbaseFeed
from crypto_directional.paper import PaperBroker
from crypto_directional.risk import RiskManager
from crypto_directional.strategy.momentum import MomentumStrategy


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def run() -> None:
    settings = Settings()
    configure_logging(__import__("os").getenv("LOG_LEVEL", "INFO"))
    log = logging.getLogger("bot")
    if settings.kill_switch:
        log.error("GLOBAL_KILL_SWITCH is enabled; refusing to start")
        return
    risk = RiskManager(settings.initial_equity, settings.risk_per_trade_pct,
                       settings.max_open_positions, settings.max_daily_loss_pct,
                       settings.max_spread_bps)
    broker = PaperBroker(settings.initial_equity, risk, settings.taker_fee_bps, settings.slippage_bps)
    strategy = MomentumStrategy()
    feed = CoinbaseFeed(settings.ws_url, settings.products)
    log.warning("PAPER MODE ONLY: no exchange orders can be submitted")
    async for tick in feed.stream():
        broker.mark(tick.product_id, tick.price, tick.receive_time)
        if tick.spread_bps > settings.max_spread_bps or tick.feed_age_ms > settings.max_feed_age_ms:
            continue
        signal = strategy.on_ticker(tick)
        if signal:
            broker.on_signal(signal, tick.spread_bps, tick.feed_age_ms, settings.max_feed_age_ms)


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logging.getLogger("bot").info("stopped by operator")


if __name__ == "__main__":
    main()
