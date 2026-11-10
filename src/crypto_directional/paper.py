from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from crypto_directional.risk import RiskManager
from crypto_directional.strategy.momentum import Signal

log = logging.getLogger(__name__)


@dataclass
class Position:
    product_id: str
    side: str
    quantity: float
    entry: float
    stop: float
    target: float
    opened_at: datetime


class PaperBroker:
    def __init__(self, equity: float, risk: RiskManager, fee_bps: float,
                 slippage_bps: float, max_hold_minutes: int = 120):
        self.cash = equity
        self.risk = risk
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.max_hold_minutes = max_hold_minutes
        self.positions: dict[str, Position] = {}

    def on_signal(self, signal: Signal, spread_bps: float, feed_age_ms: float,
                  max_feed_age_ms: int) -> None:
        decision = self.risk.approve(signal, spread_bps, len(self.positions), feed_age_ms, max_feed_age_ms)
        if not decision.approved or signal.product_id in self.positions:
            log.info("paper signal rejected", extra={"product": signal.product_id, "reason": decision.reason or "already open"})
            return
        direction = 1 if signal.side == "long" else -1
        fill = signal.entry_reference * (1 + direction * (self.slippage_bps / 10_000))
        fee = abs(fill * decision.quantity) * self.fee_bps / 10_000
        self.cash -= fee
        self.positions[signal.product_id] = Position(
            signal.product_id, signal.side, decision.quantity, fill,
            signal.stop_price, signal.target_price, datetime.now(UTC),
        )
        log.info("paper position opened", extra={"product": signal.product_id, "side": signal.side,
                 "quantity": decision.quantity, "entry": fill, "fee": fee, "score": signal.score})

    def mark(self, product_id: str, price: float, now: datetime) -> None:
        position = self.positions.get(product_id)
        if not position:
            return
        age_min = (now - position.opened_at).total_seconds() / 60
        hit_stop = price <= position.stop if position.side == "long" else price >= position.stop
        hit_target = price >= position.target if position.side == "long" else price <= position.target
        if hit_stop or hit_target or age_min >= self.max_hold_minutes:
            direction = 1 if position.side == "long" else -1
            exit_price = price * (1 - direction * self.slippage_bps / 10_000)
            gross = (exit_price - position.entry) * position.quantity * direction
            fees = abs(exit_price * position.quantity) * self.fee_bps / 10_000
            net = gross - fees
            self.cash += net
            self.risk.equity = self.cash
            log.info("paper position closed", extra={"product": product_id, "reason": "stop" if hit_stop else "target" if hit_target else "time",
                     "gross_pnl": gross, "fees": fees, "net_pnl": net, "cash": self.cash})
            del self.positions[product_id]
