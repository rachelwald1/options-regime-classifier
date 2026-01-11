from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


Trend = Literal["up", "down", "sideways"]
Objective = Literal["speculate", "income", "hedge"]


@dataclass(frozen=True, slots=True)
class OptionSnapshot:
    """
    A single snapshot of the underlying + one option contract + your intent.

    Notes:
    - iv is a decimal (e.g. 0.32 for 32%)
    - iv_rank is 0–100
    - bid_ask_spread_pct is percent of mid (e.g. 0.6 means 0.6%)
    - theta is typically per-day (platform-dependent); keep consistent across your inputs
    - vega units vary by platform; keep consistent across your inputs
    """

    # Market context
    price: float
    trend: Trend
    days_to_expiry: int
    upcoming_event: bool  # True if earnings/CPI/FOMC etc within your chosen window

    # Volatility
    iv: float            # decimal, e.g. 0.25 = 25%
    iv_rank: float       # 0..100 (or use iv_percentile if your platform provides that instead)

    # Greeks (as provided by broker/platform)
    delta: float         # calls: 0..1, puts: -1..0
    theta: float         # usually negative for long options; per-day on most platforms
    vega: float          # sensitivity to IV changes (units vary by platform)

    # Liquidity / microstructure
    bid_ask_spread_pct: float  # percent of mid, e.g. 0.8 means 0.8%

    # Your intent
    objective: Objective

    # Optional metadata (nice for logging / future extensions)
    symbol: Optional[str] = None
    option_type: Optional[Literal["call", "put"]] = None
    strike: Optional[float] = None

    def __post_init__(self) -> None:
        # Basic sanity checks to catch obvious input mistakes early.
        if self.price <= 0:
            raise ValueError("price must be > 0")

        if self.days_to_expiry <= 0:
            raise ValueError("days_to_expiry must be > 0")

        if not (0.0 <= self.iv_rank <= 100.0):
            raise ValueError("iv_rank must be between 0 and 100")

        if self.iv < 0:
            raise ValueError("iv must be >= 0 (as a decimal, e.g. 0.25 for 25%)")

        if self.bid_ask_spread_pct < 0:
            raise ValueError("bid_ask_spread_pct must be >= 0")

        # Delta sanity (allows slight model/broker rounding outside bounds)
        if self.delta < -1.05 or self.delta > 1.05:
            raise ValueError("delta looks out of range (expected roughly -1 to 1)")

        if self.option_type is not None and self.option_type not in ("call", "put"):
            raise ValueError("option_type must be 'call' or 'put' if provided")

        if self.strike is not None and self.strike <= 0:
            raise ValueError("strike must be > 0 if provided")