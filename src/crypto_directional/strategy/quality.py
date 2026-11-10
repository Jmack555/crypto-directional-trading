from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QualityEvidence:
    """Normalized, point-in-time evidence for one directional trade candidate.

    Every component is a value in [0, 1]. Values must be computed from
    closed/available data only; missing evidence must not be imputed as zero.
    """

    regime_alignment: float
    higher_timeframe_confluence: float
    setup_quality: float
    volume_confirmation: float
    relative_strength: float
    execution_quality: float
    net_reward_risk: float
    data_fresh: bool
    liquidity_pass: bool
    directional_conflict: bool
    expected_cost_to_target_ratio: float


@dataclass(frozen=True)
class QualityAssessment:
    score: float | None
    eligible: bool
    reasons: tuple[str, ...]


WEIGHTS = {
    "regime_alignment": 15.0,
    "higher_timeframe_confluence": 15.0,
    "setup_quality": 20.0,
    "volume_confirmation": 10.0,
    "relative_strength": 10.0,
    "execution_quality": 10.0,
    "net_reward_risk": 20.0,
}


def assess_trade_quality(
    evidence: QualityEvidence | None, threshold: float = 80.0
) -> QualityAssessment:
    """Return a 0-100 quality ranking and fail-closed eligibility decision.

    This is a transparent ranking score, NOT a calibrated probability or
    predicted win rate. Promotion to a probability requires separate
    chronological calibration and out-of-sample reliability testing.
    """
    if not 0.0 <= threshold <= 100.0:
        raise ValueError("threshold must be between 0 and 100")
    if evidence is None:
        return QualityAssessment(None, False, ("missing quality evidence",))

    component_names = tuple(WEIGHTS)
    values = {name: getattr(evidence, name) for name in component_names}
    for name, value in values.items():
        if not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
            return QualityAssessment(None, False, (f"invalid or missing {name}",))

    if not 0.0 <= evidence.expected_cost_to_target_ratio:
        return QualityAssessment(None, False, ("invalid cost-to-target ratio",))

    vetoes: list[str] = []
    if not evidence.data_fresh:
        vetoes.append("stale or unverified market data")
    if not evidence.liquidity_pass:
        vetoes.append("liquidity gate failed")
    if evidence.directional_conflict:
        vetoes.append("directional evidence conflict")
    if evidence.net_reward_risk < 1.5:
        vetoes.append("net reward-to-risk below 1.5")
    if evidence.expected_cost_to_target_ratio > 0.35:
        vetoes.append("estimated costs exceed 35% of target distance")
    if vetoes:
        return QualityAssessment(None, False, tuple(vetoes))

    # Net R:R contributes progressively from 1.0R to 2.5R.
    rr_component = min(1.0, max(0.0, (evidence.net_reward_risk - 1.0) / 1.5))
    components = dict(values)
    components["net_reward_risk"] = rr_component
    score = round(sum(components[name] * weight for name, weight in WEIGHTS.items()), 2)
    if score < threshold:
        return QualityAssessment(score, False, (f"quality score below {threshold:.0f}",))
    return QualityAssessment(score, True, ("quality threshold passed",))
