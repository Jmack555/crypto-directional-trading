# Trading Lessons Ledger

Append-only record of observations, hypotheses, accepted/rejected experiments, and rollbacks for the directional trading agent.

## Rules

- Never delete or overwrite a lesson or decision. Corrections are appended as new entries referencing the original ID.
- Every hypothesis links to evidence/trade IDs and a reproducible experiment ID.
- Distinguish observations from validated findings. A diagnosis is not proof of causation.
- Preserve rejected hypotheses and the reason for rejection to prevent repeated failed experiments.
- Record positive patterns from winning trades as well as failure clusters from losing trades.
- No entry in this file authorizes live trading. The current improvement loop is paper-only.

## Status definitions

- observation: initial evidence, not yet clustered or tested.
- pending_validation: falsifiable hypothesis and candidate change defined.
- accepted_shadow: passed historical gates; shadow evaluation only.
- rejected: failed validation or safety gate; retain evidence and reason.
- insufficient_evidence: sample or data quality inadequate.
- monitoring: approved paper champion/canary under observation.
- superseded: a later append-only record replaces the current interpretation.

## Append-only entries

No lessons have been validated by the automated improvement loop yet.

### Template

~~~yaml
lesson_id: L-YYYYMMDD-NNNN
created_at_utc: YYYY-MM-DDTHH:MM:SSZ
cycle_id: C-YYYYMMDD-HHMM
status: observation
kind: failure_cluster # or positive_pattern
primary_category: unknown_or_insufficient_evidence
contributing_categories: []
strategy_id: ""
strategy_version: ""
symbol_scope: []
side_scope: [long, short]
regime_scope: []
trade_ids: []
sample_size: 0
diagnosis_confidence: low
what_happened: ""
evidence_summary: ""
failed_or_successful_rule: ""
hypothesis: ""
candidate_change: ""
expected_effect: ""
possible_adverse_effect: ""
experiment_id: ""
validation_window: ""
validation_result: pending
decision_reason: ""
related_lesson_ids: []
supersedes: []
~~~

### First record

No trade-level data has been analyzed by this loop yet. Do not pre-populate lessons with hypothetical losses; create records only from observed, auditable trades.
