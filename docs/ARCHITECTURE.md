# System Architecture

## 1. Objective and boundaries

Build a reliable research-to-execution platform for directional cryptocurrency trading. It identifies opportunities where price may move up or down over a short horizon, ranks them, validates them, and manages risk.

The initial target holding period is approximately 1–2 hours, with no overnight exposure. This is a testable constraint, not a guarantee that every signal will close within that window.

**In scope:** centralized-exchange market data; technical and market-structure screening; long/short signal research; historical simulation; paper trading; portfolio risk controls; execution on approved venues; monitoring and audit logs.

**Out of scope:** CEX–DEX or DEX–DEX arbitrage, multi-hop arbitrage, MEV, sandwiching, and transaction-ordering strategies.

## 2. High-level flow

Exchange REST/WebSocket APIs → venue adapters → normalized market events → validation/time alignment → market-data store and feature engine → candidate screener → signal generation/ranking → portfolio risk engine → execution gateway → exchange orders → fills/positions/PnL → monitoring and analytics.

Backtesting and paper trading consume the same versioned feature and strategy interfaces wherever possible. Differences between historical and live data handling must be explicit and tested.

## 3. Recommended initial technology

Start with a modular Python application, not premature microservices.

| Area | Initial choice | Rationale |
|---|---|---|
| Runtime | Python 3.12+ with asyncio | Quant ecosystem and asynchronous I/O |
| Validation | Pydantic and typed interfaces | Consistent module contracts |
| Exchange access | Native venue REST/WebSocket adapters; CCXT where suitable | Common interface without losing venue-specific control |
| Analysis | Polars and NumPy | Efficient numerical and columnar processing |
| Local research store | Parquet plus DuckDB | Low-cost, reproducible research |
| Operational database | PostgreSQL; add TimescaleDB only if justified | Durable state and relational records |
| API | FastAPI | Typed operational endpoints |
| Tests | pytest | Unit, integration, and regression coverage |
| Packaging | pyproject.toml and locked dependencies | Reproducible environments |
| Deployment | Docker after local workflow stabilizes | Repeatable runtime |

Do not select paid feeds or hosting until symbols, message rates, latency, retention, and budget are measured. Exchange APIs differ in rate limits, symbol conventions, historical depth, and order semantics.

## 4. Core modules

### Venue adapters
Discover instruments, tick/lot sizes, minimum notional, trading status, and supported order types. Subscribe to trades, best bid/ask, order-book updates, and candles where available. Fetch historical candles and reconcile gaps. Normalize timestamps to UTC and symbols to canonical instrument identifiers. Handle reconnects, sequence gaps, rate limits, and maintenance.

### Data validation and storage
Validate event and receive timestamps, duplicates, out-of-order or delayed events, invalid prices, crossed books, candle discontinuities, and metadata changes. Store raw captures when practical alongside normalized trades, quotes, candles, funding rates, and instrument metadata. Record data provenance and ingestion version.

A strategy must not act on stale or unhealthy data. Staleness thresholds are venue/feed-specific configuration, not hard-coded assumptions.

### Feature engine
Compute causal, timestamped features:
- Returns and momentum across multiple lookbacks.
- Moving averages and trend slope.
- ATR and realized volatility.
- Relative volume and volume z-scores.
- VWAP distance and range position.
- Spread, depth, and order-book imbalance where reliable.
- Swing highs/lows, support/resistance zones, and breakout distance.
- Relative strength versus BTC, ETH, and a suitable market benchmark.

Every feature defines its lookback, sampling interval, warm-up, missing-data behavior, and earliest knowable timestamp.

### Candidate screener
Screen range breakouts/breakdowns, all-time and rolling highs/lows, triple tops/bottoms, volume expansion, trend continuation, momentum acceleration, volatility contraction/expansion, and reversal candidates.

Apply liquidity, spread, data-health, and instrument-eligibility filters before ranking. Pattern detectors must define objective tolerances and confirmation rules; avoid subjective chart labels.

### Signal engine and ranking
Each strategy emits a structured proposal containing instrument, venue, direction, strategy/version, event time, data watermark, entry condition, invalidation, stop, target, time-based exit, expected holding horizon, feature snapshot, estimated costs, score, and rationale codes.

Rank using independently measured factors such as trend alignment, relative volume, volatility regime, market structure, liquidity, and estimated net reward-to-risk. A score is only a ranking statistic unless calibrated and validated as a probability. Keep each setup independent so its contribution can be tested.

### Portfolio risk engine
Risk checks run after signal generation and before order submission. Required controls:
- Maximum risk per trade and aggregate open risk.
- Maximum concurrent positions and per-asset exposure.
- Correlation/concentration limits.
- Daily loss limit and drawdown circuit breaker.
- Maximum spread, slippage, and order notional.
- Data freshness and exchange-health checks.
- Position reconciliation and duplicate-order prevention.
- Time-based exit and no-overnight policy.
- Global kill switch and per-venue disable switch.

Limits are configuration-driven, logged, tested, and fail closed. Initial defaults are conservative; live trading is disabled.

### Execution gateway
Isolate venue-specific order logic behind a venue-neutral interface. Handle precision/minimums, idempotent client order IDs, acknowledgements, partial fills, cancel/replace, rejections, rate limits, safe retries, timeout reconciliation, slippage checks, and position/balance reconciliation.

Never blindly retry an order after an ambiguous timeout. Query the venue by client order ID and reconcile actual state first.

### Backtest, paper, and live modes
All modes use comparable strategy interfaces and emit comparable events.

**Backtest:** point-in-time data, causal features, fees, spread, slippage, funding, latency assumptions, partial fills, market constraints, delisted instruments where available, chronological splits, and untouched test periods. Avoid look-ahead and survivorship bias.

**Paper:** live feeds with simulated order lifecycle and realistic costs. Record signal time, simulated arrival, fills, rejects, and missed trades.

**Live:** disabled by default. Requires explicit enablement, approved venue, secrets supplied outside the repository, passing tests, and configured risk limits. Begin with minimal notional and a manual kill switch.

### Monitoring and audit
Track feed uptime/delay/gaps, reconnects, stale-data blocks, screener throughput, signal counts, signal-to-order and order-to-fill latency, rejects, partial fills, slippage, fees, funding, PnL, drawdown, exposure, and risk events.

Every decision must be reconstructable from versioned code, configuration, data references, and logs. Alert on broken feeds, unexpected positions, repeated order errors, and risk-limit breaches.

## 5. Target repository layout

    crypto-directional-trading/
    ├── README.md
    ├── pyproject.toml
    ├── .env.example
    ├── .gitignore
    ├── config/
    ├── docs/
    │   ├── ARCHITECTURE.md
    │   ├── ROADMAP.md
    │   └── STRATEGY_SPEC.md
    ├── src/directional_trading/
    │   ├── domain/
    │   ├── adapters/
    │   ├── data/
    │   ├── features/
    │   ├── screener/
    │   ├── strategies/
    │   ├── portfolio/
    │   ├── risk/
    │   ├── execution/
    │   ├── backtest/
    │   ├── paper/
    │   ├── monitoring/
    │   └── api/
    ├── tests/
    │   ├── unit/
    │   ├── integration/
    │   └── fixtures/
    ├── research/
    └── scripts/

This is a target structure, not a reason to create empty modules prematurely.

## 6. Domain objects

Define versioned typed models for Instrument, TradeEvent, QuoteEvent, OrderBookSnapshot, Candle, FundingRate, FeatureSnapshot, Candidate, Signal, RiskDecision, OrderIntent, OrderUpdate, Fill, Position, and PnLSnapshot.

Use decimal arithmetic for money and exchange quantities where precision matters. Use UTC internally and preserve exchange event time alongside local receive time.

## 7. Non-functional requirements

Correctness and traceability before raw speed. Use bounded queues/backpressure, deterministic replay, graceful reconnect and gap recovery, explicit timeouts/cancellation, structured logs with correlation IDs, and reproducible configuration. Never place secrets in source, logs, notebooks, or fixtures.

## 8. Decisions to validate with measurement

Benchmark number of venues/instruments, peak event rate, acceptable end-to-end latency, retention/query patterns, required order-book depth, provider cost/reliability, and whether a single-process async engine is sufficient.

Introduce Kafka, NATS, ClickHouse, Kubernetes, or distributed services only when measured bottlenecks justify them.
