# Agent Skills Integration Plan

## Purpose

Use five prebuilt Agent Skills as implementation playbooks for the existing Jmack555/crypto-directional-trading Python project. Skills guide the coding/research agent; they are not runtime dependencies and do not independently create alpha. The repository's typed contracts, tests, and deterministic risk engine remain authoritative.

## Scope and constraints

- Directional long/short only; no arbitrage, MEV, sandwiching, or cross-DEX execution.
- Holding period 1–120 minutes; no overnight exposure.
- Coinbase is the current market-data foundation; Kraken is a later adapter after Coinbase replay is reliable.
- Current implementation includes a Coinbase public WebSocket adapter, irregular ticker-sampled EMA prototype, paper broker, risk checks, feed freshness/reconnect handling, and CI.
- No live order-entry implementation. Paper-only remains the supported operating mode until separately reviewed and explicitly approved.

## Five skills and how to apply them

### 1. VectorBT Expert — backtesting foundation

Source: https://github.com/marketcalls/vectorbt-backtesting-skills

Install:
~~~bash
npx skills add marketcalls/vectorbt-backtesting-skills -s vectorbt-expert
~~~

Use for:
- Vectorized portfolio simulation and long/short signal evaluation.
- Fee/slippage modeling, portfolio statistics, equity curves, and drawdown analysis.
- Walk-forward and robustness-testing patterns.

Adapt before use:
- The skill documentation includes non-crypto market assumptions and OpenAlgo-specific indicators. Do not import Indian-market taxes, OpenAlgo dependencies, or its indicator conventions into this project.
- Use the project's Coinbase/Kraken normalized candles and venue-specific fee schedule.
- Keep the repository's strategy/data interfaces; VectorBT is the research engine, not a replacement for the live/paper event architecture.
- Verify VectorBT order timing and fill assumptions against the project's next-event execution model.

### 2. ML Strategy — predictive signal challenger

Source: https://github.com/HKUDS/Vibe-Trading/tree/main/agent/src/skills/ml-strategy

Install:
~~~bash
npx skills add HKUDS/Vibe-Trading -s ml-strategy
~~~

Use for:
- OHLCV feature engineering and sklearn model baselines.
- Random Forest / Gradient Boosting / Ridge-style model comparison.
- Walk-forward model training and directional prediction.

Adapt before use:
- The source skill's example features and default prediction/retraining horizons are not automatically suitable for a 1–120 minute crypto system.
- Build labels for 5m, 15m, and 60m outcomes, with executable entry assumptions, cost deductions, stop/time exits, and a flat/no-trade class.
- Use purged chronological validation and an embargo at least as long as the maximum overlapping label/holding horizon.
- Fit scalers/feature selection/calibration only on training data. Calibrate predicted probabilities on separate chronological data.
- Start with simple regularized models and Random Forest. Gradient boosting is a challenger only if it improves untouched out-of-sample net results.
- ML predictions rank/propose; they never override risk rejection.

### 3. Optimize — parameter stability, not curve fitting

Source: https://github.com/marketcalls/vectorbt-backtesting-skills

Install:
~~~bash
npx skills add marketcalls/vectorbt-backtesting-skills -s optimize
~~~

Use for:
- Predeclared parameter sweeps, heatmaps, and comparison of parameter combinations.
- Sensitivity analysis across EMA, momentum, volatility, stop, and exit parameters.

Adapt before use:
- Run parameter search only inside each training window.
- Choose stable plateaus, not a single best in-sample point.
- Track all trials and account for multiple testing/selection bias.
- Re-evaluate chosen parameters on a fresh walk-forward segment and untouched final holdout.
- Freeze the selected parameters during paper evaluation.

### 4. Risk Analysis — portfolio and tail-risk research

Source: https://github.com/HKUDS/Vibe-Trading/tree/main/agent/src/skills/risk-analysis

Install:
~~~bash
npx skills add HKUDS/Vibe-Trading -s risk-analysis
~~~

Use for:
- VaR/CVaR, maximum drawdown, volatility, Monte Carlo, historical/hypothetical stress testing, and tail-risk diagnostics.
- Offline review of strategy and portfolio return series.

Adapt before use:
- This is primarily an analytics/review workflow, not a low-latency pre-trade order gate.
- Convert useful findings into explicit, tested configuration limits in src/crypto_directional/risk.py.
- Do not copy example drawdown/daily-loss/position percentages blindly.
- Use deterministic checks for per-trade risk, aggregate open risk, exposure, correlation, daily loss, drawdown, spread/slippage, feed health, and no-overnight exit.
- Risk decisions fail closed and carry reason codes.

### 5. Algorithmic Trading — system and execution discipline

Source: https://github.com/TerminalSkills/skills/tree/main/skills/algo-trading

Install:
~~~bash
npx skills add TerminalSkills/skills -s algo-trading
~~~

Use for:
- End-to-end architecture review across data ingestion, strategy interfaces, backtesting, risk, execution, monitoring, and audit.
- Order lifecycle, idempotency, paper-first workflow, and failure testing.

Adapt before use:
- Treat generic example thresholds and live-order snippets as illustrative only.
- Preserve the project's paper-only mode and no-live-order implementation.
- Do not introduce a live exchange adapter as part of this plan.
- Any future execution work requires separate approval, reconciliation tests, and a manual kill switch.

## Integration sequence

1. Install the skills in the coding-agent workspace and inspect their complete SKILL.md instructions before using them.
2. Record the current repository baseline and run existing tests.
3. Upgrade the market-data pipeline to finalized 1m/5m/15m/1h/4h bars with deterministic replay.
4. Implement causal features and a transparent regime classifier.
5. Build independent setup modules and a stable signal contract.
6. Integrate VectorBT and execution-aware cost/fill assumptions.
7. Add ML as a challenger model using intraday labels and purged walk-forward validation.
8. Use Optimize for bounded parameter sweeps inside training folds only.
9. Use Risk Analysis for offline tail/stress reports; translate approved controls into deterministic risk code.
10. Use Algorithmic Trading as an architecture/failure-test checklist.
11. Run live-data paper trading with frozen strategy/model versions.
12. Promote nothing to live without separate explicit authorization.

## Test matrix

| Test | Baseline comparison | Pass condition |
|---|---|---|
| Signal value | Existing EMA prototype vs each independent setup | Net out-of-sample expectancy improves or the setup is rejected |
| Regime filter | Same strategy with/without regime gate | Better risk-adjusted net result without unacceptable missed edge |
| ML | Simple ranker vs ML vs combined | Challenger improves untouched holdout and calibration |
| Optimization | Default parameters vs selected stable region | Improvement persists on unseen data and neighboring settings |
| Risk | Existing checks vs expanded deterministic gates | Every limit blocks unsafe trade; fail-closed behavior verified |
| Execution model | Mid-price fills vs bid/ask + delay + costs | Promotion decision uses realistic execution results only |
| Paper | Backtest expectations vs live-data paper results | Differences are explained and within predeclared tolerance |

## Required artifacts

- Versioned feature definitions and signal schema.
- Dataset manifests and replay fixtures.
- Backtest reports with cost breakdown and chronological splits.
- Experiment registry with all trials and promotion decisions.
- Risk configuration and unit/property/failure-injection tests.
- Daily paper report by symbol, direction, strategy, regime, and model version.
- Model card recording training window, labels, features, calibration, validation, and known limitations.

## Important implementation note

The current MomentumStrategy consumes irregular ticker updates. Its EMA/momentum output is a prototype, not a validated candle-based signal. The current RiskManager checks kill switch, position count, daily loss, spread, feed age, and stop distance, but it does not yet provide full portfolio correlation/exposure control, slippage estimation, or exchange-aware quantity/price validation. These are explicit engineering gaps, not features to assume an imported skill has already supplied.
