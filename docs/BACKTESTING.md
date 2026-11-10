# Backtesting v1

The first implemented backtester is a deliberately small, inspectable baseline. It is not evidence of an edge and it does not auto-promote strategies.

## Model

- Input: chronological, timezone-aware OHLCV candles (`timestamp,open,high,low,close,volume`).
- Signal: fast EMA crosses above slow EMA on a fully closed candle.
- Entry: next candle open; no same-candle signal/fill look-ahead.
- Stop: 1.5 ATR below entry; target: 2R; max holding period: 120 bars.
- If stop and target are both touched in one candle, stop is assumed first (conservative ordering).
- Spot-only, long-only; position notional is capped at 100% of equity, no leverage.
- Risk budget defaults to 0.25% of equity per trade; at $500 that is $1.25 of planned price risk before gaps and execution costs.
- Fee, slippage, and spread are configurable and charged on both sides. Defaults are research assumptions, not a claim about the user's actual exchange tier.

## Run

```bash
python -m crypto_directional.backtest path/to/ohlcv.csv --equity 500 --fee-bps 40 --slippage-bps 5 --spread-bps 4
```

Install the package first (`pip install -e '.[dev]'`). CSV timestamps must be ISO-8601 with an explicit timezone, preferably UTC. Bars must be strictly chronological with no duplicate timestamps.

## Known limitations before strategy comparison

- EMA and ATR use a simple recursive seed; benchmark alternative seeding and warm-up lengths.
- No partial fills, queue position, order-book depth, exchange outages, funding, borrow, tax, or order rejection model.
- No portfolio-level simultaneous positions/correlation logic yet.
- Long-only spot model; short/perpetual support requires funding, margin, liquidation, and borrow models.
- Current output is one strategy run; walk-forward splits, parameter search controls, benchmark comparisons, and bootstrap confidence intervals remain to be implemented.
- Historical data must be sourced, timestamp-normalized, deduplicated, and checked for gaps before results are trusted.

Never tune parameters on the final holdout. Compare net returns, drawdown, profit factor, expectancy, turnover, and stability across instruments and regimes. A strategy with negative net expectancy after costs should be rejected regardless of win rate.
