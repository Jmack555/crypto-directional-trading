from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    ws_url: str = os.getenv("COINBASE_WS_URL", "wss://ws-feed.exchange.coinbase.com")
    products: tuple[str, ...] = tuple(
        p.strip() for p in os.getenv(
            "PRODUCT_IDS", "BTC-USD,ETH-USD,SOL-USD,XRP-USD,LTC-USD,DOGE-USD"
        ).split(",") if p.strip()
    )
    max_feed_age_ms: int = int(os.getenv("MAX_FEED_AGE_MS", "2000"))
    initial_equity: float = float(os.getenv("INITIAL_EQUITY_USD", "10000"))
    risk_per_trade_pct: float = float(os.getenv("RISK_PER_TRADE_PCT", "0.0025"))
    max_open_positions: int = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "0.02"))
    max_spread_bps: float = float(os.getenv("MAX_SPREAD_BPS", "12"))
    taker_fee_bps: float = float(os.getenv("TAKER_FEE_BPS", "60"))
    slippage_bps: float = float(os.getenv("SLIPPAGE_BPS", "5"))
    max_hold_minutes: int = int(os.getenv("MAX_HOLD_MINUTES", "120"))
    kill_switch: bool = _bool("GLOBAL_KILL_SWITCH", False)
    trading_mode: str = os.getenv("TRADING_MODE", "paper").lower()
    live_enabled: bool = _bool("LIVE_TRADING_ENABLED", False)

    def __post_init__(self) -> None:
        if self.trading_mode != "paper":
            raise ValueError("Only TRADING_MODE=paper is implemented")
        if self.live_enabled:
            raise ValueError("Live trading is not implemented; LIVE_TRADING_ENABLED must be false")
        if not self.products:
            raise ValueError("PRODUCT_IDS must contain at least one product")
        if not 0 < self.risk_per_trade_pct <= 0.01:
            raise ValueError("RISK_PER_TRADE_PCT must be in (0, 0.01]")
        if not 0 < self.max_daily_loss_pct <= 0.05:
            raise ValueError("MAX_DAILY_LOSS_PCT must be in (0, 0.05]")
