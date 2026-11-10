# Implementation Roadmap

## Guiding rule

Build and validate one vertical slice at a time. The objective is repeatable net edge after realistic costs, not maximizing indicators or trade count. No milestone automatically authorizes live trading.

## Milestone 0 — Requirements and baseline
**Deliverables**
- Confirm exchanges, spot/perpetual markets, symbols, capital assumptions, data budget, and operational environment.
- Define the 1–2 hour target and no-overnight rule precisely.
- Predefine benchmark strategies and evaluation metrics.
- Establish coding standards, dependency management, configuration, and secret handling.

**Exit gate:** Written venue/instrument/universe/timeframe/cost decisions; no secrets committed.

## Milestone 1 — Market-data foundation
**Deliverables**
- Implement one exchange adapter end to end.
- Ingest instrument metadata, trades, best bid/ask, and candles.
- Normalize symbols, quantities, timestamps, and event schemas.
- Persist historical data to Parquet and query with DuckDB.
- Add reconnect, heartbeat, gap detection, REST backfill, and stale-feed blocking.

**Exit gate:** Tests cover disconnect/reconnect and missing, duplicate, and out-of-order events. Recorded data replays deterministically. Completeness, delay, and storage volume are measured. An unhealthy feed cannot produce an eligible signal.

## Milestone 2 — Universe and screener
**Deliverables**
- Configurable universe based on liquidity, spread, market status, and data quality.
- Rolling highs/lows, breakout/breakdown, relative volume, momentum, volatility, and trend features.
- Objective triple-top/triple-bottom and swing-structure detection.
- BTC/ETH-relative strength and broad-market context.
- Ranked candidate snapshots with reason codes.

**Exit gate:** Unit tests cover warm-up, boundaries, missing candles, and timestamp alignment. Pattern definitions are deterministic. Output is reproducible from fixed data. Report candidate counts and liquidity distributions; make no performance claims yet.

## Milestone 3 — Signal research
**Deliverables**
- Independent strategy modules for each setup.
- Entry, invalidation, stop, target, maximum holding time, and no-trade conditions.
- Fees, spread, slippage, funding, and realistic execution assumptions.
- Compare simple baselines with multi-factor ranking.
- Evaluate long and short performance separately.

**Exit gate:** No look-ahead/leakage; each signal stores feature snapshot and strategy version. Report expectancy, net return, drawdown, trade count, turnover, exposure, and cost breakdown. Do not tune against the final holdout.

## Milestone 4 — Backtesting and validation
**Deliverables**
- Execution-aware simulator.
- Walk-forward evaluation across multiple market regimes.
- Untouched out-of-sample test set.
- Sensitivity analysis for costs, slippage, latency, and parameters.
- Benchmarks: no-trade, simple momentum, and simple breakout.

**Exit gate:** Signals use only information available at decision time. Results are robust enough across adjacent parameters and periods to warrant paper testing. Report gross/net performance, drawdown, tail losses, uncertainty, and cost breakdown. Reject edges that disappear under plausible costs.

## Milestone 5 — Live-data paper trading
**Deliverables**
- Run screener/strategies on live feeds without sending exchange orders.
- Simulate latency, fills, partial fills, spread crossing, fees, and missed fills.
- Compare simulated fills with contemporaneous market conditions.
- Produce daily strategy and system-health reports.

**Exit gate:** Predeclared observation period and sample size met. No unexplained simulated position drift. Feed failures and risk limits reliably block trades. Paper results are consistent with backtest assumptions within documented tolerances.

## Milestone 6 — Risk engine and execution integration
**Deliverables**
- Portfolio limits, per-trade risk, exposure/correlation caps, daily loss stop, and kill switch.
- Integrate one approved venue using test environment or minimal-risk configuration.
- Idempotent order IDs, reconciliation, partial-fill handling, and safe timeout recovery.
- Manual disable control and auditable operator actions.

**Exit gate:** Failure-injection tests cover disconnects, rate limits, rejects, partial fills, ambiguous timeouts, and restarts. No duplicate orders after recovery. Risk fails closed on stale data, missing balances, and inconsistent positions. Live mode remains disabled unless explicitly enabled.

## Milestone 7 — Limited live pilot
**Deliverables**
- Enable only after prior gates pass and the operator explicitly authorizes live use.
- Start with minimal notional and strict loss/exposure limits.
- Compare actual fills/costs/slippage with paper assumptions.
- Review every trade and incident.

**Exit gate:** Execution quality within predeclared tolerances; no unresolved critical safety/reconciliation defects; net performance reviewed after all costs.

## Milestone 8 — Optimization and expansion
**Deliverables**
- Add venues only after the first is reliable.
- Expand instruments based on liquidity and data quality.
- Improve ranking, regime detection, and portfolio allocation.
- Test features through controlled experiments and ablation.
- Automate monitoring and research reports.

**Exit gate:** Each addition improves out-of-sample results or operational quality. Changes are versioned against a stable baseline. No model or parameter update is promoted live without validation.

## Priority order

| Priority | Workstream | Rationale |
|---|---|---|
| P0 | Requirements, schemas, secrets, tests | Prevents rework and unsafe defaults |
| P0 | One reliable market-data adapter | All downstream work depends on correct data |
| P1 | Historical storage and replay | Reproducible research |
| P1 | Features and candidate screener | Converts data into testable setups |
| P1 | Independent signal modules | Fair strategy comparison |
| P1 | Backtesting and cost model | Filters false edges before capital exposure |
| P2 | Live-data paper trading | Tests operational reality |
| P2 | Risk and execution integration | Controlled, auditable orders |
| P3 | Limited live pilot | Only after evidence and explicit approval |
| P3 | Multi-venue scale and optimization | Avoids premature complexity |

## Required performance report

For every strategy and evaluation period, report trade count, win rate, average win/loss, expectancy per trade and in risk units, gross PnL, fees, spread, slippage, funding, net PnL, profit factor, maximum drawdown, time under water, exposure, turnover, holding-time distribution, missed signals, and results by direction, instrument, volatility regime, and market trend. Include uncertainty estimates when sample size permits.

Do not select a strategy by win rate alone. High win rate can still lose money when losses and costs are large.

## Immediate engineering tasks

1. Add Python project scaffolding, dependency locks, linting, and CI.
2. Define domain models and configuration schema.
3. Select the first exchange and a small liquid test universe.
4. Implement and test the first WebSocket/REST adapter.
5. Capture a reproducible dataset and build the first screener baseline.
