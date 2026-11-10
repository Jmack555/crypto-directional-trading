# 80+ Trade-Quality Execution Gate

## Purpose

The bot may paper-execute a directional signal only when a separately computed
trade-quality score is **at least 80/100** and every hard risk/data gate passes.
This is a quality-ranking threshold, not an 80% predicted win rate or a
calibrated probability of profit.

## Scorecard

| Evidence group | Weight |
|---|---:|
| Market-regime alignment | 15 |
| Higher-timeframe confluence | 15 |
| Setup / market-structure quality | 20 |
| Relative-volume confirmation | 10 |
| Relative strength versus benchmark | 10 |
| Execution quality (spread, depth, expected slippage) | 10 |
| Cost-adjusted reward/risk | 20 |
| **Total** | **100** |

Each evidence component is normalized to [0, 1] and must be computed from
point-in-time data. Cost-adjusted reward/risk contributes progressively from
1.0R to 2.5R. Avoid counting correlated indicators as independent evidence:
features are grouped by evidence family, and an ablation report must measure
the incremental value of each family.

## Hard vetoes

Regardless of score, reject when data is stale/unverified, liquidity fails,
directional evidence conflicts, net reward/risk is below 1.5R, or estimated
round-trip costs exceed 35% of target distance. Missing or invalid evidence
also rejects; it is never silently imputed.

## Current integration status

The current Coinbase ticker-only EMA prototype does not have closed-bar
higher-timeframe regime, volume, relative-strength, order-book depth, or
cost-adjusted setup evidence. It therefore emits no quality score. The risk
manager rejects such signals. **Expect zero paper entries until a causal
multi-timeframe feature pipeline supplies the complete evidence object.**
This is intentional fail-closed behavior; do not map the old EMA score to the
80-point scorecard.

## Calibration and promotion

Before interpreting scores probabilistically, collect timestamped candidate
snapshots and outcomes, split chronologically, calibrate only on training /
validation windows, and evaluate reliability on untouched out-of-sample data.
Report Brier score, log loss, calibration curve, sample count, confidence
intervals, net expectancy after fees/spread/slippage, drawdown, and results by
asset and market regime. Use purged/embargoed walk-forward splits where labels
overlap. Track every candidate, including rejected trades, to measure
selection bias and missed-opportunity behavior.

Paper-only remains mandatory. No live order adapter is enabled by this change.
