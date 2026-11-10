"""Causal, long-only spot backtester for timestamped OHLCV candles.

Signals are evaluated on a fully closed candle and orders fill at the next
candle open. If a candle touches both stop and target, stop is assumed first.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError("candle timestamps must be timezone-aware")
        if min(self.open, self.high, self.low, self.close) <= 0 or self.volume < 0:
            raise ValueError("OHLC prices must be positive and volume non-negative")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high is inconsistent with OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low is inconsistent with OHLC values")


@dataclass(frozen=True)
class BacktestConfig:
    initial_equity: float = 500.0
    risk_per_trade_pct: float = 0.0025
    max_notional_pct: float = 1.0  # spot only; no leverage
    fee_bps_per_side: float = 40.0
    slippage_bps_per_side: float = 5.0
    spread_bps: float = 4.0  # full quoted spread; half charged on each side
    fast_ema: int = 8
    slow_ema: int = 21
    atr_period: int = 14
    stop_atr: float = 1.5
    reward_risk: float = 2.0
    max_hold_bars: int = 120

    def __post_init__(self) -> None:
        if self.initial_equity <= 0:
            raise ValueError("initial_equity must be positive")
        if not 0 < self.risk_per_trade_pct <= 0.01:
            raise ValueError("risk_per_trade_pct must be in (0, 1%]")
        if not 0 < self.max_notional_pct <= 1:
            raise ValueError("spot max_notional_pct must be in (0, 1]")
        if self.fast_ema < 2 or self.slow_ema <= self.fast_ema:
            raise ValueError("EMA periods must satisfy 2 <= fast < slow")
        if self.atr_period < 2 or self.stop_atr <= 0 or self.reward_risk <= 0:
            raise ValueError("invalid ATR/exit configuration")
        if self.max_hold_bars < 1:
            raise ValueError("max_hold_bars must be positive")
        if min(self.fee_bps_per_side, self.slippage_bps_per_side, self.spread_bps) < 0:
            raise ValueError("execution costs cannot be negative")


@dataclass(frozen=True)
class Trade:
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    fees: float
    net_pnl: float
    exit_reason: str
    equity_after: float


@dataclass(frozen=True)
class BacktestResult:
    initial_equity: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    win_rate_pct: float
    profit_factor: float
    trade_count: int
    total_fees: float
    trades: tuple[Trade, ...]


def load_csv(path: str | Path) -> list[Candle]:
    """Load CSV columns timestamp,open,high,low,close,volume (ISO-8601 UTC)."""
    rows: list[Candle] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(Candle(
                timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
                volume=float(row["volume"]),
            ))
    validate_candles(rows)
    return rows


def validate_candles(candles: Iterable[Candle]) -> list[Candle]:
    data = list(candles)
    if len(data) < 3:
        raise ValueError("at least three candles are required")
    if any(data[i].timestamp >= data[i + 1].timestamp for i in range(len(data) - 1)):
        raise ValueError("candles must be strictly chronological without duplicates")
    return data


def _ema(values: list[float], period: int) -> list[float]:
    alpha = 2.0 / (period + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (1.0 - alpha) * out[-1])
    return out


def _atr(candles: list[Candle], period: int) -> list[float]:
    true_ranges = [candles[0].high - candles[0].low]
    for previous, current in zip(candles, candles[1:]):
        true_ranges.append(max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close),
        ))
    return _ema(true_ranges, period)


def run_backtest(candles: Iterable[Candle], config: BacktestConfig = BacktestConfig()) -> BacktestResult:
    data = validate_candles(candles)
    closes = [c.close for c in data]
    fast = _ema(closes, config.fast_ema)
    slow = _ema(closes, config.slow_ema)
    atr = _atr(data, config.atr_period)
    equity = config.initial_equity
    peak = equity
    max_dd = 0.0
    fees_total = 0.0
    trades: list[Trade] = []
    position: dict[str, float | int | datetime] | None = None
    cost_rate = (config.fee_bps_per_side + config.slippage_bps_per_side + config.spread_bps / 2) / 10_000

    # Last candle cannot produce an entry because there is no next-open fill.
    for i in range(1, len(data)):
        bar = data[i]
        if position is not None:
            entry = float(position["entry"])
            stop = float(position["stop"])
            target = float(position["target"])
            qty = float(position["qty"])
            held = i - int(position["entry_index"])
            exit_px: float | None = None
            reason = ""
            if bar.open <= stop:
                exit_px, reason = bar.open, "stop_gap"
            elif bar.open >= target:
                exit_px, reason = target, "target"
            elif bar.low <= stop:
                exit_px, reason = stop, "stop"
            elif bar.high >= target:
                exit_px, reason = target, "target"
            elif held >= config.max_hold_bars:
                exit_px, reason = bar.close, "time"
            if exit_px is not None:
                execution_exit = exit_px * (1.0 - cost_rate)
                gross = (exit_px - entry) * qty
                entry_fee = float(position["entry_notional"]) * config.fee_bps_per_side / 10_000
                exit_fee = exit_px * qty * config.fee_bps_per_side / 10_000
                # Slippage and spread are reflected in execution prices; fees are explicit.
                net = (execution_exit - entry) * qty - entry_fee - exit_fee
                equity += net
                fees = entry_fee + exit_fee
                fees_total += fees
                trades.append(Trade(position["entry_time"], bar.timestamp, entry, exit_px,
                                    qty, gross, fees, net, reason, equity))
                position = None
                peak = max(peak, equity)
                max_dd = max(max_dd, (peak - equity) / peak if peak > 0 else 0.0)

        if position is None and i < len(data) - 1:
            # Cross above slow EMA; all inputs are from completed candle i-1.
            signal_i = i - 1
            crossed_up = fast[signal_i] > slow[signal_i] and fast[signal_i - 1] <= slow[signal_i - 1]
            if crossed_up and atr[signal_i] > 0:
                raw_entry = bar.open
                entry = raw_entry * (1.0 + cost_rate)
                stop_distance = config.stop_atr * atr[signal_i]
                risk_budget = equity * config.risk_per_trade_pct
                qty_by_risk = risk_budget / stop_distance
                qty_by_cash = (equity * config.max_notional_pct) / entry
                qty = min(qty_by_risk, qty_by_cash)
                notional = qty * entry
                if qty > 0 and notional > 0:
                    position = {
                        "entry": entry, "stop": entry - stop_distance,
                        "target": entry + stop_distance * config.reward_risk,
                        "qty": qty, "entry_index": i, "entry_time": bar.timestamp,
                        "entry_notional": notional,
                    }

    if position is not None:
        bar = data[-1]
        exit_px = bar.close
        qty = float(position["qty"])
        entry = float(position["entry"])
        execution_exit = exit_px * (1.0 - cost_rate)
        entry_fee = float(position["entry_notional"]) * config.fee_bps_per_side / 10_000
        exit_fee = exit_px * qty * config.fee_bps_per_side / 10_000
        gross = (exit_px - entry) * qty
        fees = entry_fee + exit_fee
        net = (execution_exit - entry) * qty - entry_fee - exit_fee
        equity += net
        fees_total += fees
        trades.append(Trade(position["entry_time"], bar.timestamp, entry, exit_px,
                            qty, gross, fees, net, "end_of_data", equity))
        peak = max(peak, equity)
        max_dd = max(max_dd, (peak - equity) / peak if peak > 0 else 0.0)

    wins = sum(t.net_pnl > 0 for t in trades)
    gross_profit = sum(t.net_pnl for t in trades if t.net_pnl > 0)
    gross_loss = -sum(t.net_pnl for t in trades if t.net_pnl < 0)
    pf = gross_profit / gross_loss if gross_loss else (math.inf if gross_profit else 0.0)
    return BacktestResult(
        initial_equity=config.initial_equity, final_equity=equity,
        total_return_pct=(equity / config.initial_equity - 1) * 100,
        max_drawdown_pct=max_dd * 100,
        win_rate_pct=(wins / len(trades) * 100) if trades else 0.0,
        profit_factor=pf, trade_count=len(trades), total_fees=fees_total,
        trades=tuple(trades),
    )
