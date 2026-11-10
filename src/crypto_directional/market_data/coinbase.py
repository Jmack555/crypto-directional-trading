from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

import websockets

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Ticker:
    product_id: str
    price: float
    bid: float
    ask: float
    exchange_time: datetime
    received_monotonic: float
    receive_time: datetime

    @property
    def spread_bps(self) -> float:
        mid = (self.bid + self.ask) / 2
        return ((self.ask - self.bid) / mid * 10_000) if mid > 0 else float("inf")

    @property
    def feed_age_ms(self) -> float:
        return max(0.0, (self.receive_time - self.exchange_time).total_seconds() * 1000)


class CoinbaseFeed:
    """Public Coinbase Exchange ticker stream with bounded reconnect backoff."""

    def __init__(self, url: str, products: tuple[str, ...]):
        self.url = url
        self.products = products

    async def stream(self) -> AsyncIterator[Ticker]:
        delay = 0.5
        while True:
            try:
                async with websockets.connect(
                    self.url, ping_interval=20, ping_timeout=20,
                    close_timeout=5, max_queue=4096,
                ) as ws:
                    await ws.send(json.dumps({
                        "type": "subscribe",
                        "product_ids": list(self.products),
                        "channels": ["ticker", "heartbeat"],
                    }))
                    log.info("connected to Coinbase feed", extra={"products": self.products})
                    delay = 0.5
                    async for raw in ws:
                        received_mono = time.monotonic()
                        received_at = datetime.now(timezone.utc)
                        try:
                            msg = json.loads(raw)
                            if msg.get("type") != "ticker":
                                continue
                            product = msg.get("product_id")
                            price, bid, ask = (float(msg[k]) for k in ("price", "best_bid", "best_ask"))
                            exchange_time = datetime.fromisoformat(msg["time"].replace("Z", "+00:00"))
                            if product not in self.products or min(price, bid, ask) <= 0 or bid > ask:
                                continue
                            yield Ticker(product, price, bid, ask, exchange_time, received_mono, received_at)
                        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                            log.debug("ignored malformed or non-ticker message")
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Coinbase feed disconnected; reconnecting")
                await asyncio.sleep(delay + random.uniform(0, delay * 0.2))
                delay = min(delay * 2, 30.0)
