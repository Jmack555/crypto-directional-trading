# Strategy Research Specification

## Purpose

Define measurable directional setups for research. These are hypotheses to test, not claims of profitability. Keep every setup independent so its contribution can be measured.

## Initial timeframe model

- 1m/5m: entry timing, spread, and short-term execution context.
- 15m: primary setup and confirmation context.
- 1h/4h: broader trend, levels, and regime context.
- Intended duration: approximately 1–2 hours.
- Time-based exit: close/reduce positions before configured maximum holding time and no-overnight cutoff.

All timeframes and holding limits are configuration values and must be tested against the selected venue and strategy.

## Candidate setup families

### A. Range breakout / breakdown
Hypothesis: a confirmed move beyond a defined consolidation range, with meaningful participation, may continue.

Specify range window and minimum observations, volatility/tick-size breakout buffer, close/trade confirmation, relative-volume threshold, maximum chase distance, invalidation, and time stop. Measure false-breakout rate after realistic entry delay.

### B. Rolling high/low and all-time high/low
Define whether the reference is exchange listing history, available dataset history, or a rolling period. Never label a level an all-time high/low if history is incomplete; record coverage.

### C. Triple top / triple bottom
Hypothesis: repeated tests of a price zone may indicate absorption and breakout or rejection and reversal.

Specify pivot identification, number/spacing of tests, ATR-scaled zone tolerance, minimum reaction between tests, confirmation trigger, invalidation, and treatment of unequal highs/lows. Three nearby candles do not constitute a pattern; require distinct swing tests separated by meaningful reactions.

### D. Relative-volume expansion
Compare activity against a time-of-day and instrument-appropriate baseline where possible. Separate quote volume from base-asset volume and account for venue reporting differences.

### E. Momentum and trend continuation
Candidate features: multi-window returns, moving-average slope/alignment, price versus VWAP, and higher-timeframe trend state. Test features individually before combining them.

### F. Volatility contraction / expansion
Identify compression with a defined range/volatility measure, then test expansion with directional confirmation. Volatility alone does not establish direction.

### G. Relative strength
Compare instrument returns with BTC, ETH, and a broad liquid-market benchmark over matching windows. Align timestamps and exclude stale or unavailable benchmark observations.

## Signal contract

Every signal includes instrument, venue, direction, strategy name/version, signal timestamp, source-data watermark, entry rule and maximum acceptable price, stop/invalidation, target/exit logic, maximum holding time, no-overnight expiry, expected fees/spread/slippage/funding, feature snapshot, score, and reason codes.

A score is a ranking statistic until calibration demonstrates that it represents a probability.

## Ranking and selection

Begin with transparent factors: higher-timeframe trend alignment, setup quality, relative volume, momentum/relative strength, volatility suitability, spread/depth/liquidity, estimated net reward-to-risk, and portfolio concentration/correlated exposure.

Use a simple baseline first. Add weights or machine learning only when out-of-sample tests demonstrate robust improvement.

## Evaluation protocol

- Use point-in-time data and causal features.
- Split chronologically; never randomly mix future and past observations.
- Use walk-forward evaluation and an untouched final holdout.
- Include fees, spread, slippage, funding, and realistic order constraints.
- Report long and short results separately.
- Evaluate by regime, instrument, and holding-time bucket.
- Include parameter sensitivity and ablation tests.
- Account for multiple testing when exploring many patterns/parameters.
- Preserve failed experiments to reduce repeated overfitting.

## Minimum comparison baselines

1. No-trade/cash baseline.
2. Simple time-series momentum.
3. Simple breakout without multi-factor ranking.
4. Each individual setup family.
5. Combined screener and ranker.

## Promotion rule

Research may move to paper only with reproducible results, no identified leakage, positive net expectancy in relevant out-of-sample tests with uncertainty reported, plausible robustness to higher costs and execution delay, and defined risk/invalidation/time-exit behavior.

Paper-to-live promotion requires a separate operational review, minimum paper observation period, tested risk controls, and explicit operator approval.
