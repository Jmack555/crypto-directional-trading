# Twice-Daily Trading Improvement Loop

## Purpose and safety boundary

The improvement engine reviews closed directional trades, diagnoses outcomes, writes durable lessons, proposes narrowly scoped strategy changes, and validates each candidate before promotion.

It is a research and paper-trading process. The existing system is paper-only. This loop must not add live exchange order submission, change live credentials, or promote any candidate to real-money execution. ML/LLM components may classify, explain, and propose; deterministic validation and risk code control all state transitions.

Scope: directional long/short, 1–120 minute holding period, no overnight exposure. Arbitrage, MEV, sandwiching, and cross-DEX strategies are out of scope.

## Schedule and cycle semantics

Default schedule: 00:00 UTC and 12:00 UTC every day. Also support an optional session-close trigger, but deduplicate it against scheduled cycles using a canonical cycle window.

- Use UTC everywhere.
- Each cycle processes trades closed after the last successfully committed checkpoint and at or before the cycle's fixed cutoff time.
- Capture cutoff time once at cycle start. Late-arriving trade records whose close time is before the cutoff are picked up by the next cycle using a reconciliation lookback; do not silently skip them.
- Use a distributed/process lock so two cycles cannot mutate the same state concurrently.
- Assign a deterministic cycle ID from schedule window and cutoff. Re-running the same cycle is idempotent.
- Deduplicate trades by immutable venue/account/trade-or-position identifier. If one position closes in multiple fills, aggregate fills into one logical closed-trade record while preserving each fill.
- Persist raw inputs and intermediate outputs before advancing the checkpoint. Advance the checkpoint only after all required artifacts have been written and verified.
- On failure, retain the prior checkpoint, mark the cycle failed/partial, and safely retry. Never mark a partially processed cycle complete.

## Cycle pipeline

### 1. Ingest

Read every newly closed trade from the canonical trade ledger, including:
- immutable trade and position IDs; venue, symbol, side, strategy/setup and version;
- signal, feature, model, regime and risk-decision snapshots at entry;
- entry/exit timestamps, prices, quantities, partial fills and exit reason;
- realized gross and net PnL, fees, spread/slippage estimates, funding, and currency;
- intended/actual stop, target, hold duration, risk-at-entry, leverage and exposure;
- quote/order-book and feed-health snapshots when available.

Normalize to a canonical schema and calculate net PnL consistently. Separate profitable, unprofitable, and flat/near-zero outcomes using a configurable tolerance that accounts for fees and rounding. Preserve raw source records; never rewrite trade history.

Also ingest a sample of winning trades for positive-pattern discovery. A losing-only review would create a one-sided learning bias.

Data-quality rules:
- Quarantine records with missing IDs, impossible timestamps, inconsistent quantities, or unreconciled PnL.
- Do not infer missing fill prices, fees, news, or market state.
- Keep an explicit missing/unknown state.
- Reconcile late-arriving records using a bounded overlap window plus ID deduplication.

### 2. Diagnose

Assign one primary failure category and zero or more contributing categories to each losing trade. Store evidence, confidence, and whether the category is actionable. Allowed taxonomy:

1. bad_market_regime_or_trend_reversal
2. signal_decay_or_false_breakout
3. poor_entry_timing_or_chasing
4. stop_loss_or_take_profit_misplacement
5. risk_sizing_vs_volatility
6. slippage_liquidity_fees
7. news_or_event_shock
8. correlation_or_concentration
9. overfitting_or_parameter_drift
10. data_feed_or_execution_fault
11. unknown_or_insufficient_evidence

Diagnostic evidence should use the entry-time regime/features and subsequent path, not hindsight-only information presented as if it were available at entry. News/event classification requires a timestamped source; absent evidence, use unknown. Distinguish root cause from symptoms (e.g. stop hit is not itself proof the stop was misplaced).

For winners, identify positive contributors using the same feature/regime/signal snapshots and record them as positive_pattern rather than forcing a failure label.

### 3. Cluster and extract lessons

Cluster trades by category, strategy/setup version, symbol/liquidity class, regime, side, and similar feature context. Avoid merging unrelated failures just because they share a broad label.

Only create a cluster-level lesson when the minimum evidence threshold is met (default 5 related trades); otherwise create a provisional single-trade observation, clearly marked low confidence.

Every lesson record contains:
- immutable lesson ID and creation cycle;
- linked trade IDs and experiment IDs;
- what happened and evidence summary;
- primary/secondary categories;
- affected strategy, rule, feature, parameter, or risk gate;
- confidence and sample size;
- testable hypothesis with expected direction of effect;
- exact candidate change and its scope;
- validation design, metrics, pass criteria and holdout dates;
- status: observation, pending_validation, accepted_shadow, rejected, superseded, or monitoring;
- decision rationale and links to prior related lessons.

A lesson must be concise, falsifiable, and specific. Example: "For breakout setup v3 in low-volatility range regimes, requiring relative volume >= 1.3 is hypothesized to improve net expectancy; test against the unchanged baseline on the next chronological holdout." Do not make broad changes based on a single trade.

### 4. Propose minimal updates

The engine may propose:
- a single parameter adjustment or bounded parameter range;
- one additional/modified signal filter;
- one regime eligibility rule;
- one risk limit or sizing calculation;
- one execution constraint;
- a skill instruction or research workflow change.

Each proposal must identify one hypothesis, one smallest practical change, affected files/config, expected benefit, possible adverse effect, and a rollback plan. Prefer one-variable/one-rule experiments. Do not combine several unrelated changes into one candidate because attribution becomes impossible.

Do not allow an LLM to edit production code, production parameters, risk limits, or installed skills directly. It creates a candidate patch/branch and experiment specification for deterministic CI and review. Skill changes are versioned candidate artifacts and must pass the same evaluation.

Before proposing a previously tested idea, search LESSONS.md and the experiment registry. If the hypothesis matches a rejected experiment, either do not repeat it or explain what changed (new data, regime, venue, execution model) and assign a new linked experiment ID.

### 5. Validate before deployment

Use the same data contracts, feature definitions, execution model, and cost assumptions as the baseline. The candidate and baseline must be evaluated on identical timestamps, symbols, eligible opportunities, and starting capital.

Validation protocol:
- chronological train/validation/holdout splits; never random-shuffle time series;
- all feature transformations fit on training data only;
- purge overlapping labels and embargo at least the maximum forward label/holding horizon;
- parameter search occurs only in training folds;
- reserve a final untouched holdout; do not repeatedly tune against it;
- walk-forward evaluation across more than one market regime where data permits;
- account for maker/taker fees, spread, slippage, latency, partial/missed fills, funding where applicable, and conservative fill assumptions;
- report long and short separately and break down by symbol, regime, setup and holding-time bucket;
- compare candidate and champion on the same out-of-sample trades/opportunities;
- bootstrap trade outcomes or use another suitable uncertainty estimate; disclose low sample size and multiple-testing/selection bias.

Required side-by-side metrics:
- net and gross PnL, with fees/spread/slippage/funding breakdown;
- net expectancy per trade and in risk units;
- win rate;
- profit factor;
- Sharpe and Sortino;
- maximum drawdown and time under water;
- trade count, exposure, turnover and holding-time distribution.

### 6. Default promotion gates

These are conservative starting defaults, not universal guarantees. Make them explicit configuration and tune only through a separately reviewed policy change.

A candidate is eligible for paper shadow only if all apply:
- at least 100 closed holdout trades for the candidate/baseline comparison; require more for highly variable or fragmented strategies;
- net expectancy improvement >= 5% relative to champion, with the 95% bootstrap confidence interval for the paired expectancy difference above zero;
- profit factor >= 1.05 and not below champion;
- Sharpe and Sortino do not deteriorate by more than 5% relative to champion (if baseline metric is near zero/negative, use absolute guardrails and human review rather than a misleading ratio);
- maximum drawdown does not worsen by more than 5% relative;
- candidate trade count is at least 70% of champion unless a separately documented risk-reduction case justifies lower activity;
- no material degradation in either long or short side, no catastrophic regime-specific failure, and no breached hard risk limit;
- results remain acceptable under conservative cost and execution-delay stress tests.

Win rate is mandatory to report, not a mandatory improvement target: higher payoff asymmetry can improve expectancy while reducing win rate. If any required metric is unavailable, sample size is inadequate, uncertainty is too high, or criteria conflict, the candidate is not promoted. Record rejected or insufficient_evidence; never loosen thresholds automatically to make a candidate pass.

### 7. Safe deployment states

State machine:
proposed -> validating -> rejected | shadow -> canary_paper -> champion_paper

- rejected: retain report and reason; no production change.
- shadow: compute candidate signals alongside champion but do not alter paper orders.
- canary_paper: allocate a configurable minority of paper opportunities/capital to candidate while champion remains intact; no real orders.
- champion_paper: candidate may become the active paper strategy only after shadow/canary review and explicit human approval.
- rolled_back: revert active paper configuration to last known-good champion; preserve candidate and all evidence.

Default canary allocation: 10% of paper allocation/opportunities, configurable. Require at least 50 additional shadow/canary trades and a minimum 7 calendar days before champion promotion, unless a separately approved study design specifies a longer period. The live trading mode remains disabled. No automatic real-money deployment is permitted by this loop.

### 8. Persist learning and audit history

Append-only artifacts:
- LESSONS.md: human-readable lesson records; never delete or rewrite old entries.
- experiments/registry.jsonl: one immutable JSON object per proposal, validation, acceptance, rejection, or rollback event.
- experiments/reports/<experiment_id>/: frozen config, dataset manifest, baseline/candidate metrics, cost assumptions, plots/tables, and validation logs.
- state/improvement_checkpoint.json: last committed close-time cursor, last cycle ID, reconciliation window, and artifact checksums.
- state/improvement_cycles/<cycle_id>.json: cycle status, input IDs/counts, stage status, errors, and output references.

Corrections are new append-only events that reference the superseded record. Never edit historical trades, lessons, or experiment decisions in place. Store only non-secret identifiers and redact credentials/account secrets.

## Reliability, monitoring, and tests

- Idempotency test: replay the same cycle twice; no duplicate lesson, experiment, or trade ingestion.
- Checkpoint test: crash after each pipeline stage; retry must neither skip nor double-count records.
- Late-arrival test: close-time records arriving after the cutoff are picked up by reconciliation.
- Data integrity test: missing fills/fees/quotes lead to quarantine or explicit uncertainty, not fabricated values.
- Leakage test: future features, labels, and holdout observations cannot enter training or parameter selection.
- Metric test: baseline and candidate use identical costs, fills, timestamps, and capital.
- Gate test: each threshold independently blocks promotion when breached.
- Audit test: every proposal, rejection, approval, shadow transition and rollback is append-only and traceable.
- Safety test: no code path from the improvement loop can submit a live exchange order or change live credentials.
- Operational metrics: cycle duration, last successful cycle, trade ingestion lag, quarantine count, diagnosis coverage, experiments proposed/passed/rejected, checkpoint age, and failure alerts.

## Cycle output

Each run produces a concise report containing:
1. Cycle ID, cutoff, status, and checkpoint range.
2. Trades ingested: total, winners, losers, flat, quarantined.
3. Failure taxonomy counts and highest-confidence clusters.
4. New lesson IDs and linked trades.
5. Proposed experiments and affected components.
6. Validation results for every completed experiment, with baseline/candidate metrics.
7. Accepted-to-shadow, rejected, or insufficient-evidence decisions and reasons.
8. Any operational/data-quality alert.
9. Updated checkpoint and artifact references.

## Implementation order

1. Define canonical closed-trade schema and append-only ledger.
2. Implement scheduler, cycle lock, idempotency keys, and transactional checkpoint.
3. Implement taxonomy classifier with evidence and unknown state.
4. Implement clustering and lesson/experiment appenders.
5. Implement isolated candidate branches/configs and experiment registry.
6. Implement reproducible walk-forward validation and metric report.
7. Implement hard promotion gates and paper-only shadow/canary state machine.
8. Add crash/replay/late-data/leakage/safety tests.
9. Enable 00:00 and 12:00 UTC schedules only after manual test cycles pass.

Do not activate the scheduler until all reliability and safety tests pass. This specification does not claim the loop is already implemented or running.
