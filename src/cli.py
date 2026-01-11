from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.models import OptionSnapshot
from src.classifier import classify


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Classify options market regime from a JSON snapshot (decision support, not trading advice)."
    )
    parser.add_argument(
        "--snapshot",
        type=str,
        default="data/sample_option_snapshot.json",
        help="Path to a JSON file containing an OptionSnapshot-compatible object",
    )
    args = parser.parse_args()

    path = Path(args.snapshot)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")

    raw = json.loads(path.read_text())
    snap = OptionSnapshot(**raw)
    result = classify(snap)

    print("\nOptions Regime Classification")
    print("-" * 30)
    if snap.symbol:
        print(f"Symbol: {snap.symbol}")
    print(f"Objective: {snap.objective}")
    print(f"IV Rank: {snap.iv_rank:.0f}")
    print(f"DTE: {snap.days_to_expiry}")
    print(f"Bid–ask spread: {snap.bid_ask_spread_pct:.2f}%")

    print("\nSuggested posture:", result["action"])
    print("Confidence:", result["confidence"])
    print("\nReasons:")
    for r in result["reasons"]:
        print(f"- {r}")
    print("")


if __name__ == "__main__":
    main()
