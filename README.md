# Options Regime Classifier

A rules-based decision-support tool that classifies **options market conditions**
to help determine whether the current environment is more suitable for:

- buying option premium (long volatility),
- selling option premium (short volatility),
- hedging existing exposure,
- or standing aside.

This project is **educational and analytical**.  
It does **not** generate trade recommendations, predict prices, or place trades.

---

## Motivation

Options trading is difficult because profitability depends on more than price
direction. Time decay, implied volatility, liquidity, and event risk can dominate
outcomes even when the underlying moves as expected.

Many poor decisions come from skipping a basic question:

> *“Does this trade make sense in the current market environment?”*

This project formalises that question into an explicit, testable rules engine.

---

## What this tool does

Given a snapshot of market and option data, the classifier:

1. Evaluates the **volatility regime** using IV Rank
2. Assesses **time-to-expiry (DTE)** and gamma/theta risk
3. Applies **liquidity filters** using bid–ask spread
4. Flags **event risk** (earnings, macro releases)
5. Incorporates the user’s **objective** (speculate / income / hedge)

It then outputs:
- a suggested **posture** (e.g. buy premium, sell premium, hedge, do nothing)
- a **confidence level**
- a list of **human-readable reasons**

---

## Project structure

```text
options-regime-classifier/
├── src/
│   ├── models.py        # Domain model (OptionSnapshot)
│   ├── config.py        # Heuristic thresholds
│   ├── classifier.py   # Regime classification logic
│   └── cli.py           # Command-line interface
├── tests/
│   └── test_classifier.py
├── data/
│   └── sample_option_snapshot.json
├── requirements.txt
└── README.md
