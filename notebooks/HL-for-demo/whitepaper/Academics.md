# Economic & Academic Foundations

The unified factor model is designed to be consistent with:

- **No‑arbitrage / APT thinking** – assets are linear combinations of common factors plus idiosyncratic terms.
- **Pricing‑kernel / SDF approaches** – risk premia arise from covariance with the stochastic discount factor.
- **Observed empirical behavior** of Buyout PE and VC as documented in the academic literature.

## 1. Smoothing, Desmoothing, and True Risk

Appraisal‑based private equity returns are known to be **smoothed** and to **understate true volatility**.

Key references:

- Sorensen & Jagannathan (2014): discuss how appraisal smoothing hides the true covariance with
  the pricing kernel, and argue for **Public Market Equivalent (PME)** and SDF‑consistent approaches.
- Ang, Chen, Goetzmann & Phalippou (2018): detail how appraisal smoothing affects inference about
  risk and suggest methods to uncover true private equity risk.

Our model side‑steps appraisal smoothing by:

1. Building a structural risk model from **public, liquid factors**.
2. Using desmoothed fund returns only as a **secondary calibration layer**, not as the primary risk estimator.

## 2. Leverage, Credit Cycles, and Buyout Risk

Buyout PE relies heavily on debt financing. Deal activity and returns depend on:

- credit spreads,
- lender risk appetite,
- covenant quality,
- refinancing conditions.

Key references:

- Axelson, Jenkinson, Strömberg & Weisbach (2013): show that credit market conditions strongly
  influence LBO leverage and pricing.
- Harris, Jenkinson & Kaplan (2014): document long‑run performance patterns of PE relative to public markets.

This supports the inclusion of a **credit spread factor (CS)** as a core driver.

## 3. Innovation, Tech Cycles, and VC Risk

VC returns are linked to:

- technology and innovation waves,
- intangible capital investment,
- IPO windows and exit markets.

Key references:

- Nanda & Rhodes‑Kropf (2013): show that innovation waves and disagreement affect startup funding and outcomes.
- Pástor & Veronesi (2009, 2012): model how changing growth expectations affect valuations, especially in tech.
- Kortum & Lerner (2000): link VC funding to innovation and patenting.

These justify an **innovation factor (INNOV)** derived from the relative performance
of tech‑heavy indexes versus small‑cap benchmarks (e.g. Nasdaq vs Russell 2000).

## 4. Tail Risk and Volatility Shocks

Private assets exhibit **non‑linear** behavior in crises: drawdowns are larger than predicted by Gaussian models.

Key references:

- Kelly, Jiang & Xiu (2019): develop tail risk measures for cross‑sectional pricing.
- Ang, Hodrick, Xing & Zhang (2006): volatility risk and its pricing in equity returns.
- Sorensen & Jagannathan (2014): emphasize that standard linear factor models miss some tail behavior in PE.

We capture this with a **TAIL factor** built from positive VIX changes, transformed via \\( \log(1 + z^+) \\)
to preserve extreme moves while keeping the factor numerically well‑behaved.
