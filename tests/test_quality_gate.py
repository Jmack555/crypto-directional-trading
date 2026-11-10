from crypto_directional.risk import RiskManager
from crypto_directional.strategy.momentum import Signal
from crypto_directional.strategy.quality import QualityEvidence, assess_trade_quality


def evidence(**overrides):
    values = {
        "regime_alignment": 0.95,
        "higher_timeframe_confluence": 0.95,
        "setup_quality": 0.95,
        "volume_confirmation": 0.90,
        "relative_strength": 0.90,
        "execution_quality": 0.95,
        "net_reward_risk": 2.5,
        "data_fresh": True,
        "liquidity_pass": True,
        "directional_conflict": False,
        "expected_cost_to_target_ratio": 0.20,
    }
    values.update(overrides)
    return QualityEvidence(**values)


def signal(quality_score=None):
    return Signal("BTC-USD", "long", 100.0, 99.0, 102.0, 0.9, "test", quality_score)


def test_high_quality_evidence_passes_threshold():
    result = assess_trade_quality(evidence())
    assert result.eligible
    assert result.score is not None and result.score >= 80


def test_missing_evidence_fails_closed():
    result = assess_trade_quality(None)
    assert not result.eligible
    assert result.score is None


def test_hard_veto_overrides_high_score():
    result = assess_trade_quality(evidence(data_fresh=False))
    assert not result.eligible
    assert "stale" in result.reasons[0]


def test_cost_or_rr_vetoes():
    assert not assess_trade_quality(evidence(net_reward_risk=1.4)).eligible
    assert not assess_trade_quality(evidence(expected_cost_to_target_ratio=0.36)).eligible


def test_risk_manager_rejects_missing_or_low_score():
    risk = RiskManager(500.0, 0.0025, 3, 0.02, 12.0)
    assert not risk.approve(signal(), 2.0, 0, 10, 2000).approved
    assert not risk.approve(signal(79.99), 2.0, 0, 10, 2000).approved


def test_risk_manager_accepts_score_at_or_above_threshold():
    risk = RiskManager(500.0, 0.0025, 3, 0.02, 12.0)
    decision = risk.approve(signal(80.0), 2.0, 0, 10, 2000)
    assert decision.approved
    assert decision.quantity > 0
