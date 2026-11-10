from __future__ import annotations

from dataclasses import dataclass

from crypto_directional.strategy.momentum import Signal


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    quantity: float = 0.0
    reason: str = ""


class RiskManager:
    def __init__(
        self,
        equity: float,
        risk_pct: float,
        max_positions: int,
        max_daily_loss_pct: float,
        max_spread_bps: float,
        min_quality_score: float = 80.0,
    ):
        if not 0.0 <= min_quality_score <= 100.0:
            raise ValueError("min_quality_score must be between 0 and 100")
        self.equity = equity
        self.start_of_day_equity = equity
        self.risk_pct = risk_pct
        self.max_positions = max_positions
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_spread_bps = max_spread_bps
        self.min_quality_score = min_quality_score
        self.kill_switch = False

    def approve(self, signal: Signal, spread_bps: float, open_positions: int,
                feed_age_ms: float, max_feed_age_ms: int) -> RiskDecision:
        if self.kill_switch:
            return RiskDecision(False, reason="global kill switch")
        if signal.quality_score is None:
            return RiskDecision(False, reason="missing trade-quality score; fail closed")
        if signal.quality_score < self.min_quality_score:
            return RiskDecision(False, reason=f"quality score below {self.min_quality_score:.0f}")
        if open_positions >= self.max_positions:
            return RiskDecision(False, reason="position limit")
        if self.start_of_day_equity - self.equity >= self.start_of_day_equity * self.max_daily_loss_pct:
            self.kill_switch = True
            return RiskDecision(False, reason="daily loss limit; kill switch engaged")
        if spread_bps > self.max_spread_bps:
            return RiskDecision(False, reason="spread too wide")
        if feed_age_ms > max_feed_age_ms:
            return RiskDecision(False, reason="stale market data")
        distance = abs(signal.entry_reference - signal.stop_price)
        if distance <= 0:
            return RiskDecision(False, reason="invalid stop distance")
        risk_budget = self.equity * self.risk_pct
        return RiskDecision(True, quantity=risk_budget / distance, reason="quality and risk gates approved for paper")
