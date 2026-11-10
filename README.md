# Crypto Directional Trading

A research-to-paper-trading system for short-horizon directional crypto strategies. Initial target holding period: 1–120 minutes; no overnight exposure.

**Scope:** directional long/short signals only. Arbitrage, MEV, sandwiching, and cross-DEX execution are excluded.

## Current implementation

- Coinbase Exchange public WebSocket market-data adapter (no API key required for public feeds).
- Local event-time 1-minute bar builder and EMA momentum baseline.
- Conservative paper portfolio with spread/fee/slippage assumptions and hard risk gates.
- Feed freshness checks, reconnect backoff, structured logs, and a global stop flag.
- No live order-entry implementation. `TRADING_MODE=paper` is the only supported mode; real-money execution is intentionally unavailable until separately designed, tested, and explicitly approved.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
python -m crypto_directional.main
```

The bot subscribes to the configured Coinbase USD spot products and prints paper signals/trades. It does not need exchange credentials. Start with the small default universe; do not increase subscriptions until feed health and resource use are measured.

## Configuration

Environment variables override defaults. See `.env.example` and `config/default.env`. Never commit real credentials. Public market-data mode requires no keys.

## Development

```bash
pytest
ruff check .
```

## Design documents

- [Architecture](docs/ARCHITECTURE.md)
- [Implementation roadmap](docs/ROADMAP.md)
- [Strategy research specification](docs/STRATEGY_SPEC.md)
- [Feed and execution benchmark plan](docs/FEED_AND_EXECUTION.md)

## Operating principle

Optimize for repeatable **net** expectancy after fees, spread, slippage, funding (where applicable), and missed/partial fills—not trade count, indicator count, or win rate. A signal score is not a calibrated probability. Backtests must use point-in-time data and chronological out-of-sample evaluation. Paper performance is not proof of live profitability.
