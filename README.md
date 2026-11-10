# Crypto Directional Trading

Research, screen, validate, and execute short-horizon directional cryptocurrency trades. Initial target holding period: 1–2 hours, with no overnight exposure.

**Scope:** directional long/short strategies only. Arbitrage, MEV, sandwiching, and cross-DEX execution are explicitly excluded.

## Start here
- [System architecture](docs/ARCHITECTURE.md)
- [Implementation roadmap](docs/ROADMAP.md)
- [Strategy research specification](docs/STRATEGY_SPEC.md)

## System workflow
Market data → validation and storage → features → candidate screener → signal ranking → portfolio risk checks → paper/live execution → monitoring and analytics.

## Project status
Architecture and roadmap are documented. This repository is not yet a live trading bot. Real-money execution remains disabled until the data, backtesting, paper-trading, and risk-control gates are passed.

## Principles
1. Measure net performance after fees, spread, slippage, and funding.
2. Never use future information in features, signals, or backtests.
3. Treat missing, stale, or inconsistent market data as a reason not to trade.
4. Keep signal generation separate from portfolio risk and order execution.
5. Record every input, signal, decision, order, fill, and error.
6. Start with research and paper mode; live execution requires explicit operator approval.

## Initial assumptions
- Holding-period target: 1–2 hours; no intentional overnight positions.
- Initial universe: liquid markets on explicitly supported exchanges.
- 1m/5m data for entry context; 15m/1h/4h for setup and trend context.
- Long and short signals are evaluated independently; shorting is enabled only where the venue and instrument support it.
- These are research defaults, not claims of profitability.

## Security
Never commit API keys, exchange secrets, private account data, or production environment files. Use environment variables and a local untracked .env file. Start with read-only market-data access where possible.
