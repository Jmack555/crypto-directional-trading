from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from crypto_directional.market_data.coinbase import Ticker


@dataclass(frozen=True)
class Signal:
    product_id: str
    side: str
    entry_reference: float
    stop_price: float
    target_price: float
    score: float
    reason: str


class MomentumStrategy:
    """Transparent EMA trend baseline; a research hypothesis, not a profit claim."""

    def __init__(self, fast: int = 8, slow: int = 21, history: int = 100):
        if fast >= slow:
            raise ValueError("fast EMA must be shorter than slow EMA")
        self.fast, self.slow = fast, slow
        self.prices: dict[str, deque[float]] = {}
        self.last_signal: dict[str, str] = {}

    @staticmethod
    def _ema(values: list[float], period: int) -> float:
        alpha = 2 / (period + 1)
        result = values[0]
        for value in values[1:]:
            result = alpha * value + (1 - alpha) * result
        return result

    def on_ticker(self, tick: Ticker) -> Signal | None:
        # Ticker updates are irregular. This baseline is intentionally a prototype;
        # production research must aggregate exchange-time bars and replay them causally.
        history = self.prices.setdefault(tick.product_id, deque(maxlen=500))
        history.append(tick.price)
        if len(history) < self.slow + 5:
            return None
        values = list(history)
        fast = self._ema(values[-self.fast * 3 :], self.fast)
        slow = self._ema(values[-self.slow * 3 :], self.slow)
        momentum = values[-1] / values[-min(6, len(values))] - 1
        direction = "long" if fast > slow and momentum > 0 else "short" if fast < slow and momentum < 0 else "flat"
        if direction == "flat" or self.last_signal.get(tick.product_id) == direction:
            return None
        self.last_signal[tick.product_id] = direction
        risk = max(tick.price * 0.004, 0.00000001)
        entry = tick.ask if direction == "long" else tick.bid
        stop = entry - risk if direction == "long" else entry + risk
        target = entry + 1.5 * risk if direction == "long" else entry - 1.5 * risk
        score = min(1.0, abs(momentum) * 1000 + abs(fast / slow - 1) * 100)
        return Signal(tick.product_id, direction, entry, stop, target, score, "EMA alignment + short momentum")
