from datetime import datetime, timedelta, timezone

import pytest

from crypto_directional.backtest import BacktestConfig, Candle, run_backtest, validate_candles


def make_candles(closes):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i, close in enumerate(closes):
        prev = closes[i - 1] if i else close
        bars.append(Candle(start + timedelta(minutes=i), (prev + close) / 2,
                           max(prev, close) * 1.002, min(prev, close) * 0.998,
                           close, 1000.0))
    return bars


def test_requires_timezone_and_strict_order():
    with pytest.raises(ValueError, match="timezone-aware"):
        Candle(datetime(2025, 1, 1), 100, 101, 99, 100, 1)
    bars = make_candles([100, 101, 102])
    with pytest.raises(ValueError, match="strictly chronological"):
        validate_candles([bars[0], bars[0], bars[2]])


def test_flat_market_produces_no_trades_and_preserves_equity():
    result = run_backtest(make_candles([100.0] * 100))
    assert result.trade_count == 0
    assert result.final_equity == pytest.approx(500.0)


def test_backtest_is_bounded_by_spot_cash_and_costs_reduce_returns():
    closes = [100.0] * 30 + [100 + i * 1.2 for i in range(1, 70)]
    bars = make_candles(closes)
    gross = run_backtest(bars, BacktestConfig(fee_bps_per_side=0, slippage_bps_per_side=0, spread_bps=0))
    net = run_backtest(bars, BacktestConfig(fee_bps_per_side=40, slippage_bps_per_side=5, spread_bps=4))
    assert gross.trade_count >= 1
    assert net.total_fees > 0
    assert net.final_equity < gross.final_equity
    assert all(t.quantity * t.entry_price <= 500.01 for t in net.trades)


def test_rejects_invalid_risk_and_nonchronological_data():
    with pytest.raises(ValueError):
        BacktestConfig(risk_per_trade_pct=0.02)
    with pytest.raises(ValueError):
        run_backtest(make_candles([100, 101, 102])[::-1])
