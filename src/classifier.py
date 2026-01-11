from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Literal, TypedDict

from src.models import OptionSnapshot
from src import config


Action = Literal[
    "BUY PREMIUM (prefer defined-risk spreads)",
    "SELL PREMIUM (use defined-risk structures)",
    "HEDGE (prefer spreads/collars for cost control)",
    "DO NOTHING",
]

Confidence = Literal["low", "medium", "high"]


class Classification(TypedDict):
    action: Action
    confidence: Confidence
    reasons: List[str]


def _vol_regime(iv_rank: float) -> Literal["low", "mid", "high"]:
    if iv_rank <= config.IV_RANK_LOW:
        return "low"
    if iv_rank >= config.IV_RANK_HIGH:
        return "high"
    return "mid"


def classify(snapshot: OptionSnapshot) -> Classification:
    """
    Classify an options market 'posture' based on volatility regime, time-to-expiry,
    event risk, and liquidity. This is decision support / regime classification,
    not a trade signal.
    """
    reasons: List[str] = []

    # 1. Liquidity guardrail
    if snapshot.bid_ask_spread_pct > config.MAX_BID_ASK_SPREAD_PCT:
        return {
            "action": "DO NOTHING",
            "confidence": "low",
            "reasons": [
                f"Liquidity filter: bid–ask spread {snapshot.bid_ask_spread_pct:.2f}% "
                f"> {config.MAX_BID_ASK_SPREAD_PCT:.2f}% threshold"
            ],
        }
    reasons.append(
        f"Liquidity OK: bid–ask spread {snapshot.bid_ask_spread_pct:.2f}% "
        f"≤ {config.MAX_BID_ASK_SPREAD_PCT:.2f}%"
    )

    # 2. Time-to-expiry guardrail
    if snapshot.days_to_expiry < config.MIN_DTE and snapshot.objective != "hedge":
        return {
            "action": "DO NOTHING",
            "confidence": "low",
            "reasons": [
                f"Very short DTE ({snapshot.days_to_expiry}) < {config.MIN_DTE}: "
                "gamma/theta risk is high (avoid unless explicitly hedging)"
            ],
        }

    if snapshot.days_to_expiry < config.MIN_DTE:
        reasons.append(
            f"Very short DTE ({snapshot.days_to_expiry}) < {config.MIN_DTE}: "
            "gamma/theta risk is high"
        )

    # 3. Volatility regime
    regime = _vol_regime(snapshot.iv_rank)
    if regime == "low":
        reasons.append(f"IV Rank low ({snapshot.iv_rank:.0f}) → options relatively cheap")
    elif regime == "high":
        reasons.append(f"IV Rank high ({snapshot.iv_rank:.0f}) → options relatively expensive")
    else:
        reasons.append(f"IV Rank mid ({snapshot.iv_rank:.0f}) → neutral volatility regime")

    # 4. Event risk
    if snapshot.upcoming_event:
        reasons.append(
            f"Upcoming event within ~{config.EVENT_LOOKAHEAD_DAYS} days → IV distortion/IV crush risk likely"
        )

    # 5. DTE preference guidance
    if config.PREFERRED_MIN_DTE <= snapshot.days_to_expiry <= config.PREFERRED_MAX_DTE:
        reasons.append(
            f"DTE in preferred window ({config.PREFERRED_MIN_DTE}–{config.PREFERRED_MAX_DTE})"
        )
    elif snapshot.days_to_expiry < config.PREFERRED_MIN_DTE:
        reasons.append(
            f"DTE below preferred window (<{config.PREFERRED_MIN_DTE}) → higher gamma/theta sensitivity"
        )
    else:
        reasons.append(
            f"DTE above preferred window (>{config.PREFERRED_MAX_DTE}) → more vega/carry, less capital efficient"
        )

    # 6. Objective-driven posture selection
    action: Action = "DO NOTHING"

    if snapshot.objective == "speculate":
        # Speculation: prefer long premium when IV is cheap and time isn't too short.
        if regime == "low" and snapshot.days_to_expiry >= config.PREFERRED_MIN_DTE and not snapshot.upcoming_event:
            action = "BUY PREMIUM (prefer defined-risk spreads)"
            reasons.append("Objective = speculate: low IV + enough time + no event → better conditions to buy premium")
        elif regime == "high":
            action = "SELL PREMIUM (use defined-risk structures)"
            reasons.append("Objective = speculate: high IV → consider selling premium rather than buying it")
        else:
            action = "DO NOTHING"
            reasons.append("Objective = speculate: no clear edge from regime/time/event filters")

    elif snapshot.objective == "income":
        # Income: typically short premium, but avoid doing it when IV is very low.
        if regime == "high" and config.MIN_DTE <= snapshot.days_to_expiry <= config.PREFERRED_MAX_DTE:
            action = "SELL PREMIUM (use defined-risk structures)"
            reasons.append("Objective = income: high IV + workable DTE → premium-selling conditions")
        elif regime == "low":
            action = "DO NOTHING"
            reasons.append("Objective = income: low IV → premium often too small for risk taken")
        else:
            action = "DO NOTHING"
            reasons.append("Objective = income: neutral setup")

    elif snapshot.objective == "hedge":
        # Hedging: if IV is low, protection is cheaper; if IV is high, prefer cost-controlled structures.
        if regime == "low" and snapshot.days_to_expiry >= 30:
            action = "HEDGE (prefer spreads/collars for cost control)"
            reasons.append("Objective = hedge: low IV + longer DTE → protection relatively cheaper")
        elif regime == "high":
            action = "HEDGE (prefer spreads/collars for cost control)"
            reasons.append("Objective = hedge: high IV → protection expensive; consider spreads/collars to reduce cost")
        else:
            action = "HEDGE (prefer spreads/collars for cost control)"
            reasons.append("Objective = hedge: hedge can be staged/scaled to reduce timing risk")

    else:
        action = "DO NOTHING"
        reasons.append("Unknown objective (expected: speculate / income / hedge)")

    # 7. Confidence heuristic (simple + explainable)
    confidence: Confidence = "medium"

    if snapshot.upcoming_event and action.startswith("BUY"):
        confidence = "low"
        reasons.append("Confidence lowered: buying premium into an event risks IV crush")

    if snapshot.days_to_expiry < config.PREFERRED_MIN_DTE and action != "HEDGE (prefer spreads/collars for cost control)":
        confidence = "low"
        reasons.append("Confidence lowered: short DTE increases gamma/theta instability")

    if regime in ("high", "low") and not snapshot.upcoming_event and config.PREFERRED_MIN_DTE <= snapshot.days_to_expiry <= config.PREFERRED_MAX_DTE:
        if action != "DO NOTHING":
            confidence = "high"
            reasons.append("Confidence raised: strong vol regime + preferred DTE window + no event")

    return {"action": action, "confidence": confidence, "reasons": reasons}