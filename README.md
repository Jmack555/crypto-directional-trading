# Crypto Directional Trading

A research-to-paper-trading system for short-horizon directional crypto
strategies. The initial target holding period is 1–120 minutes with no
overnight exposure. The strategy engine and execution venue are deliberately
separated.

**Strategy scope:** directional signals only. Arbitrage, MEV, sandwiching, and
cross-DEX arbitrage are not part of this project.

## Implemented

- Coinbase Exchange public WebSocket ticker/heartbeat feed (no API key needed
  for public market data).
- Experimental tick-sampled EMA paper-trading baseline with stale-feed,
  spread, kill-switch, and position-risk gates.
- Causal, long-only spot OHLCV backtester: closed-candle signals, next-open
  fills, ATR stop, 2R target, max holding period, and configurable fees,
  spread, and slippage.
- Coinbase public historical candle downloader with bounded 300-candle
  pagination, UTC normalization, deduplication, retries, and CSV export.
- A separate non-custodial Base Uniswap v3 single-hop executor, with mocked
  Foundry tests and a constrained deployment script for Base Sepolia/Base.
- GitHub Actions for Python lint/tests and Solidity build/tests.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
pytest
ruff check .
python -m crypto_directional.main
```

The live feed process is **paper-only**. It does not submit exchange orders.
Do not add exchange credentials or enable real-money trading until a separately
reviewed execution adapter and operational controls exist.

## Historical data and backtesting

See [historical data ingestion](docs/HISTORICAL_DATA.md) and
[backtesting v1](docs/BACKTESTING.md). Example:

```python
from datetime import UTC, datetime
from crypto_directional.market_data.history import (
    download_coinbase_history,
    write_candles_csv,
)

bars = download_coinbase_history(
    "BTC-USD",
    datetime(2025, 1, 1, tzinfo=UTC),
    datetime(2025, 2, 1, tzinfo=UTC),
    granularity=60,
)
write_candles_csv(bars, "data/raw/BTC-USD-1m.csv")
```

Run the resulting CSV through:

```bash
python -m crypto_directional.backtest data/raw/BTC-USD-1m.csv \
  --equity 500 --fee-bps 40 --slippage-bps 5 --spread-bps 4
```

Backtest fees are assumptions. Replace them with the actual venue/account fee
schedule and include realistic spread, slippage, liquidity, partial fills,
latency, and funding where applicable. A backtest is not evidence of a live
edge; use chronological out-of-sample validation and never tune on the final
holdout.

## Smart contract

The Base executor is a separate execution primitive, not an autonomous bot or
a profitability engine. See [contracts/README.md](contracts/README.md) for
scope, tests, deployment sequence, and security limitations. The contract has
passed mocked Foundry unit tests and CI compilation; it has **not** completed a
Base Sepolia live integration test, independent audit, or mainnet deployment.
Do not deploy to mainnet or fund it before those gates pass.

Never commit private keys, seed phrases, exchange secrets, or RPC credentials.
