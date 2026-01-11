"""
TESTS FOR OPTIONS REGIME CLASSIFIER

Each test checks that a specific heuristic or guardrail behaves as intended
when given a controlled OptionSnapshot input. 

The goal is to ensure that:

- Liquidity constraints are always enforced
- Extremely short-dated options are treated cautiously
- Low implied volatility favours long-premium postures
- High implied volatility favours short-premium postures
- User objectives (speculate / income / hedge) are respected
- Event risk appropriately reduces confidence
- Invalid or nonsensical inputs are rejected early

"""

import pytest

from src.models import OptionSnapshot
from src.classifier import classify


def make_snapshot(**overrides) -> OptionSnapshot:
    """Helper: create a valid baseline snapshot then override fields per test."""
    base = dict(
        price=100.0,
        trend="sideways",
        days_to_expiry=35,
        upcoming_event=False,
        iv=0.30,
        iv_rank=50.0,
        delta=0.30,
        theta=-0.03,
        vega=0.10,
        bid_ask_spread_pct=0.4,
        objective="speculate",
    )
    base.update(overrides)
    return OptionSnapshot(**base)


def test_liquidity_filter_blocks_trade():
    s = make_snapshot(bid_ask_spread_pct=2.5)
    result = classify(s)
    assert result["action"] == "DO NOTHING"
    assert result["confidence"] == "low"
    assert any("Liquidity filter" in r for r in result["reasons"])


def test_short_dte_blocks_non_hedge():
    s = make_snapshot(days_to_expiry=3, objective="speculate")
    result = classify(s)
    assert result["action"] == "DO NOTHING"
    assert result["confidence"] == "low"
    assert any("Very short DTE" in r for r in result["reasons"])


def test_low_iv_speculate_prefers_buy_premium():
    s = make_snapshot(iv_rank=20.0, days_to_expiry=35, upcoming_event=False, objective="speculate")
    result = classify(s)
    assert result["action"].startswith("BUY PREMIUM")
    assert result["confidence"] in ("medium", "high")
    assert any("IV Rank low" in r for r in result["reasons"])


def test_high_iv_speculate_prefers_sell_premium():
    s = make_snapshot(iv_rank=75.0, objective="speculate")
    result = classify(s)
    assert result["action"].startswith("SELL PREMIUM")
    assert any("IV Rank high" in r for r in result["reasons"])


def test_income_high_iv_prefers_sell_premium_in_workable_dte():
    s = make_snapshot(iv_rank=80.0, objective="income", days_to_expiry=45)
    result = classify(s)
    assert result["action"].startswith("SELL PREMIUM")
    assert any("Objective = income" in r for r in result["reasons"])


def test_income_low_iv_does_nothing():
    s = make_snapshot(iv_rank=10.0, objective="income")
    result = classify(s)
    assert result["action"] == "DO NOTHING"
    assert any("low iv" in r.lower() for r in result["reasons"])


def test_hedge_always_returns_hedge_posture():
    s = make_snapshot(objective="hedge", iv_rank=50.0)
    result = classify(s)
    assert result["action"].startswith("HEDGE")


def test_buy_into_event_lowers_confidence_when_buying():
    s = make_snapshot(iv_rank=20.0, objective="speculate", upcoming_event=True, days_to_expiry=35)
    result = classify(s)
    if result["action"].startswith("BUY PREMIUM"):
        assert result["confidence"] == "low"
        assert any("IV crush" in r for r in result["reasons"])


def test_models_validation_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        _ = make_snapshot(price=-1)

    with pytest.raises(ValueError):
        _ = make_snapshot(days_to_expiry=0)

    with pytest.raises(ValueError):
        _ = make_snapshot(iv_rank=200.0)

    with pytest.raises(ValueError):
        _ = make_snapshot(bid_ask_spread_pct=-0.1)
