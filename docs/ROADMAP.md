# Implementation Roadmap — Directional Trading

## Guiding rule

Build one measurable vertical slice at a time. Optimize for repeatable net, out-of-sample, risk-adjusted expectancy, not trade count, win rate, model complexity, or gross backtest return. No milestone authorizes live trading. Directional long/short only; arbitrage, MEV, sandwiching, and cross-DEX execution remain explicitly out of scope.

## Fixed operating constraints

- Intended holding period: 1–120 minutes; no overnight exposure.
- Initial venue foundation: Coinbase public market data; add Kraken after Coinbase data/replay is stable.
- Research and paper trading first. Live order entry remains unavailable until separately designed, tested, and explicitly approved.
- All results include fees, bid/ask spread, slippage, latency, partial/missed fills, and funding where the instrument requires it.
- Use the same versioned feature and signal contracts in research, backtest, and paper modes.
- ML may propose or rank signals; deterministic risk code has final authority to approve or reject every order.

## Milestone 0 — Baseline, contracts, and reproducibility

**Deliverables**
- Preserve the current Coinbase adapter, ticker-sampled EMA prototype, paper broker, feed-health checks, and CI as the baseline.
- Freeze a baseline commit and record current behavior before changing strategy logic.
- Define canonical instrument, trade, quote, candle, feature, signal, risk-decision, order-intent, fill, position, and PnL schemas.
- Define event-time and receive-time semantics, UTC timestamps, data provenance, strategy/model/config versions, and deterministic replay IDs.
- Pin Python dependencies and record reproducible environment instructions.
- Keep secrets out of Git; public market-data mode must continue to work without credentials.

**Exit gate:** baseline tests pass; a captured feed can be replayed deterministically; all signal and risk decisions are auditable.

## Milestone 1 — Reliable multi-resolution market data

**Deliverables**
- Upgrade from irregular ticker-sampled indicators to exchange-time OHLCV bars; retain raw trades/quotes where useful.
- Build 1m and 5m execution/entry bars, 15m setup bars, and 1h/4h context bars from causally aligned data.
- Add historical REST backfill, Parquet storage, DuckDB research queries, gap detection, duplicate/out-of-order handling, and candle finalization rules.
- Measure event age, receive delay, reconnects, gap rate, processing time, and p50/p95/p99 by venue and symbol.
- Add Kraken only after Coinbase adapter/replay tests pass; normalize venue-specific symbol and quantity metadata.
- Stale, incomplete, crossed, or unhealthy data must block signal eligibility.

**Exit gate:** deterministic historical replay; no trading signals from stale or incomplete feeds; adapter tests cover reconnects, gaps, duplicates, out-of-order events, and clock alignment.

## Milestone 2 — Causal feature and signal-processing layer

**Deliverables**
- Create a single feature pipeline shared by backtest and paper modes.
- Features: multi-window returns/momentum, EMA slope/alignment, ATR, realized volatility, range position, VWAP distance, relative volume/z-score, breakout distance, swing structure, BTC/ETH-relative strength, spread/depth, and order-book imbalance only when data quality supports it.
- Every feature declares lookback, sampling interval, warm-up, missing-data behavior, source timestamp, and earliest knowable timestamp.
- Preserve independent setup modules: range breakout/breakdown, rolling high/low, objective triple top/bottom, trend continuation, momentum acceleration, volatility contraction/expansion, and relative strength.
- Signal contract includes direction, setup/version, event time, data watermark, entry limit, invalidation, stop, target, maximum hold, no-overnight expiry, estimated costs, feature snapshot, score, and reason codes.
- Add reason-coded no-trade outcomes; flat/uncertain is a valid model decision.

**Exit gate:** unit tests prove features are causal and time-aligned; each setup is independently reproducible and benchmarkable.

## Milestone 3 — Regime detection and directional signal ranking

**Deliverables**
- First implement a transparent regime classifier: trend/range state, trend strength, realized-volatility bucket, volatility expansion/contraction, liquidity/spread state, and broad-market direction.
- Regimes are computed from data available at decision time and can return unknown; unknown or unsupported regimes suppress new entries by default.
- Evaluate setup-specific eligibility by regime. Breakout continuation and range mean-reversion must not share an untested universal threshold.
- Establish a simple, interpretable weighted ranker before introducing ML.
- Add ML Strategy as a challenger model, not an immediate replacement: train long/flat/short predictions on OHLCV-derived features for 5m, 15m, and 60m forward horizons aligned to the 1–120 minute holding constraint.
- Replace the source skill's daily-oriented default horizons and retraining assumptions with intraday, event-time-aware labels and retraining cadence.
- Label outcomes using executable entry/exit assumptions and net returns after estimated costs; avoid labels that assume fills at candle close when that was not executable.
- Use chronological walk-forward splits, purge overlapping labels, add an embargo at least as long as the maximum label/holding horizon, fit preprocessing only on training folds, and calibrate probabilities on separate chronological data.
- Compare simple logistic/Ridge and Random Forest baselines before more complex models. Record model version, training window, feature schema, calibration, and prediction timestamp.

**Exit gate:** ML and regime layers beat or complement the transparent baseline on untouched chronological holdouts; no look-ahead, label overlap leakage, or preprocessing leakage. ML is not allowed to bypass risk gates.

## Milestone 4 — VectorBT backtesting and execution-aware validation

**Deliverables**
- Integrate VectorBT as a research/backtest tool behind the repository's strategy and data contracts; do not let a skill-specific folder structure dictate production architecture.
- Backtest long and short separately and together, with next-eligible-event execution, bid/ask-aware entry/exit, realistic maker/taker fees, spread, slippage, latency, partial fills, missed fills, order constraints, and funding where applicable.
- Benchmark: no-trade/cash, current EMA baseline, simple momentum, simple breakout, each independent setup, regime-filtered strategy, ML-only, and combined ensemble.
- Use chronological train/validation/test partitions, rolling walk-forward evaluation, a final untouched holdout, and regime/instrument/side/holding-time breakdowns.
- Add realistic-cost stress tiers, entry-delay tests, slippage shocks, parameter-neighborhood sensitivity, trade-order Monte Carlo/bootstrap, and ablation tests.
- Track experiment registry: hypothesis, data snapshot, code/config/model version, parameter search space, trial count, metrics, and promotion decision.
- Correctly account for multiple testing and selection bias; never choose a strategy solely by its best in-sample parameter set.

**Required report:** trade count; net expectancy per trade and in risk units; gross/net PnL; fees/spread/slippage/funding; profit factor; Sharpe/Sortino; max drawdown and time under water; tail losses; exposure; turnover; holding-time distribution; long/short split; regime split; uncertainty estimates; and comparison with baselines.

**Exit gate:** positive and robust net expectancy on unseen data, credible sample size, plausible cost/delay stress tolerance, and no material performance collapse across adjacent parameter values. If not, retain research-only status.

## Milestone 5 — Parameter optimization without overfitting

**Deliverables**
- Use the Optimize skill/VectorBT parameter sweeps only inside training windows.
- Optimize a small, predeclared parameter set; avoid searching dozens of loosely justified indicators and thresholds.
- Rank parameter regions by out-of-fold stability, net expectancy, drawdown, turnover, and cost sensitivity—not by peak in-sample return.
- Prefer broad stable plateaus over a narrow optimum.
- Re-run selected parameters through a fresh walk-forward evaluation and untouched final holdout.
- Freeze parameters/model versions during paper evaluation; changes restart the evaluation window.

**Exit gate:** selected settings remain robust on data not used in selection and are not materially worse under plausible fee, spread, slippage, and delay shocks.

## Milestone 6 — Deterministic risk engine and portfolio controls

**Deliverables**
- Extend the current RiskManager; do not delegate order approval to an LLM or ML model.
- Validate stop direction/distance, target/stop consistency, minimum notional/lot/tick rules, and maximum acceptable entry price.
- Size from risk budget divided by stop distance, then cap by notional, liquidity/market impact, per-asset exposure, and portfolio exposure.
- Add aggregate open risk, concurrent position, correlated exposure, maximum turnover, daily loss, rolling drawdown, consecutive-loss cooldown, per-symbol/per-venue disable, and global kill-switch controls.
- Add regime/data-quality gates, spread and estimated-slippage ceilings, stale quote checks, venue-health checks, and no-new-entry windows near the no-overnight cutoff.
- Risk analytics skill supplies VaR/CVaR, Monte Carlo, historical/hypothetical stress scenarios, and tail diagnostics for offline risk review. These analytics inform limits but do not replace hard real-time gates.
- Use conservative configurable limits; do not copy generic example percentages from external skills as production settings.
- Use decimal-safe arithmetic for price, quantity, and money; fail closed on missing balances, unknown positions, stale data, or invalid metadata.
- Persist every allow/reject decision with machine-readable reason codes.

**Exit gate:** unit, property, and failure-injection tests prove every limit blocks correctly; portfolio risk is computed across correlated positions; all unsafe/unknown states fail closed.

## Milestone 7 — Live-data paper trading and shadow evaluation

**Deliverables**
- Run the frozen strategy on live feeds without exchange order submission.
- Simulate order arrival delay, bid/ask fills, partial fills, rejects, cancel/replace, missed fills, fees, spread, slippage, and funding.
- Compare simulated fills to contemporaneous quotes/order book; log signal-to-decision and decision-to-fill latency.
- Produce daily and weekly reports by strategy, model version, symbol, side, regime, and holding-time bucket.
- Run risk-analysis stress reports on realized paper returns and hypothetical liquidity/volatility shocks.
- Require a predeclared minimum observation window and sample size; do not promote based on a short profitable streak.

**Exit gate:** paper results are consistent with backtest assumptions within documented tolerances; no unexplained position/PnL drift; risk gates and feed failure blocks work reliably.

## Milestone 8 — Execution readiness review (still disabled by default)

**Deliverables**
- Design a separate venue execution gateway with idempotent client order IDs, precision/minimum validation, partial-fill handling, safe timeout reconciliation, cancel/replace, and position/balance reconciliation.
- Add testnet or exchange sandbox tests where supported; failure-injection tests for disconnects, rate limits, rejects, ambiguous timeouts, restarts, and duplicate messages.
- Require explicit operator approval, a manual kill switch, minimal initial notional, and strict configured exposure/loss limits.
- Keep live mode disabled in code/config until a separate authorization decision.

**Exit gate:** no unresolved critical execution/reconciliation defect; all risk and operational checks pass; explicit user approval is obtained. This roadmap does not itself authorize live trading.

## Milestone 9 — Controlled improvement loop

**Deliverables**
- Run scheduled research jobs to refresh data, calculate features, evaluate regime drift, retrain candidate models, and compare challengers against the frozen champion.
- Promote a challenger only after the full validation protocol and a new paper observation period.
- Monitor feature drift, prediction calibration, regime distribution, net expectancy, cost drift, drawdown, and operational reliability.
- Roll back automatically to the last approved version or disable a strategy when predeclared health/performance limits fail.
- Expand symbols/venues only when data quality, liquidity, and out-of-sample evidence justify it.

**Exit gate:** every change is versioned, reproducible, compared against a stable baseline, and independently approved before any live promotion.

## Priority order

| Priority | Workstream | Main skill contribution |
|---|---|---|
| P0 | Baseline, data contracts, deterministic replay | Algorithmic Trading |
| P0 | Causal feature pipeline and bar aggregation | ML Strategy + Algorithmic Trading |
| P1 | Regime classifier and signal ranking | ML Strategy |
| P1 | Execution-aware backtest and reporting | VectorBT Expert |
| P1 | Walk-forward, stress, and robustness testing | VectorBT Expert + Risk Analysis |
| P1 | Parameter search and stability selection | Optimize |
| P1 | Deterministic portfolio risk gates | Risk Analysis + Algorithmic Trading |
| P2 | Live-feed paper trading and drift monitoring | All five |
| P3 | Execution readiness and limited pilot review | Algorithmic Trading |

## Non-negotiable promotion criteria

A strategy/model cannot advance because its in-sample return is high, its win rate looks good, or an agent says it is confident. Promotion requires reproducible out-of-sample net edge, robustness to realistic costs and delay, stable behavior across relevant regimes, acceptable drawdown/tail risk, complete auditability, passing operational tests, and explicit approval for any live mode.
