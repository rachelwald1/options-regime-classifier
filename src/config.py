"""
Configuration and thresholds for options regime classification.

All values here are intentionally simple and interpretable.
They are not optimised for profitability — they encode common
options risk-management heuristics.
"""

"""
Parameter groups:

1. Volatility regime (IV Rank)
   - Measures how expensive options are relative to their own history.
   - Low IV Rank suggests options are cheap; high IV Rank suggests they are expensive.

2. Time-to-expiry (DTE)
   - Controls theta decay and gamma risk.
   - Very short DTE options are unstable; mid-range DTE offers better risk balance.

3. Liquidity constraints
   - Ensures prices are reliable and slippage does not dominate outcomes.

4. Risk heuristics
   - Flags options where time decay is aggressive relative to premium paid.

5. Event handling
   - Accounts for known events (earnings, macro releases) that distort implied volatility.
"""

# -----------------------------
# Volatility regime thresholds
# -----------------------------

# IV Rank cutoffs (0–100)
IV_RANK_LOW = 30.0        # options relatively cheap
IV_RANK_HIGH = 60.0       # options relatively expensive


# -----------------------------
# Time-to-expiry (DTE) windows
# -----------------------------

# Very short-dated options: high gamma & theta acceleration
MIN_DTE = 7

# Preferred window for most non-event trades
PREFERRED_MIN_DTE = 21
PREFERRED_MAX_DTE = 60


# -----------------------------
# Liquidity constraints
# -----------------------------

# Maximum acceptable bid–ask spread as % of mid price
MAX_BID_ASK_SPREAD_PCT = 1.0


# -----------------------------
# Risk heuristics
# -----------------------------

# If absolute daily theta exceeds this fraction of option price,
# time decay is considered aggressive.
# (Used later once option price is included)
MAX_THETA_FRACTION = 0.03


# -----------------------------
# Event handling
# -----------------------------

# Number of days before a known event during which IV distortion
# is assumed to be significant
EVENT_LOOKAHEAD_DAYS = 7