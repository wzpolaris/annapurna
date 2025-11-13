
# Hamilton Lane Private Assets Fund – Structural Risk Analysis

## 1. Objective

This note applies the unified private-markets structural model to the **Hamilton Lane Private Assets Fund (HLPAF)**.
We use:

- the Fund&apos;s **reported monthly Class R returns**, and
- the Fund&apos;s **portfolio composition** (strategy, sector, geography, investment type)

to:

1. Evaluate the usefulness of the reported returns for risk estimation.
2. Apply the **structural factor model** with overlays tailored to HLPAF.
3. Compare its implied risk to the **S&P 500** in the same factor space.
4. Discuss expected behavior in **crisis scenarios**.

The analysis is designed for **risk analytics**, not for manager selection.

## 2. Reported Returns and Desmoothing

Using the Class R monthly net performance from September 2020 through August 2025, we compute:

- average monthly return ≈ **1.2%**
- annualized mean ≈ **15%**
- monthly volatility ≈ **1.6%**
- annualized volatility ≈ **5–6%**
- maximum drawdown over the period ≈ **–1.7%**

These numbers are extraordinarily smooth for a multi-asset private-equity fund with
high buyout and growth exposure. The monthly return path rarely shows large negative months,
and even in **2022**—a year with substantial public-equity drawdowns—the Fund reports a
**+15%** calendar-year return with no deep monthly loss.

To test for standard appraisal smoothing (where reported returns follow:

    r_t = alpha + phi * r_{t-1} + u_t

with phi &gt; 0), we estimate an AR(1) model on the monthly returns:

- estimated **AR(1) coefficient**: φ ≈ –0.22 (slightly negative)
- desmoothed series using:

      r*_t = (r_t – φ r_{t-1}) / (1 – φ)

yields:

- desmoothed monthly volatility ≈ **1.3%**
- desmoothed annualized volatility ≈ **4–5%**

In other words: **standard AR(1) desmoothing actually reduces volatility slightly**, because
the reported series does not exhibit strong positive autocorrelation. The issue is not
classic &quot;AR(1) smoothing&quot; but rather that the reported NAV time series itself evolves
in a very stable, low-volatility way.

**Conclusion:** From a risk-analytics perspective, the reported monthly return series is
**not informative about the true underlying risk** of the private assets. Its volatility and
drawdown profile are much lower than what the Fund&apos;s strategy mix, leverage, and market
exposure would imply. For risk modeling, we should rely on a **structural factor model**
rather than the raw reported returns.

## 3. Structural Factor Model

We use the unified factor representation:

\[
r^{Priv}_t = \beta_{SC} SC_t
           + \beta_{CS} CS_t
           + \beta_{INNOV} INNOV_t
           + \beta_{TAIL} TAIL_t
           + \varepsilon_t,
\]

where:

- **SC** – small-cap equity factor (e.g., IWM or global small-cap ETF)
- **CS** – credit spread factor (HY vs Treasuries residual, or HY OAS changes)
- **INNOV** – innovation/tech factor, built from a 6-month moving average of (Nasdaq 100 – Russell 2000)
- **TAIL** – tail factor from positive ΔVIX transformed as `TAIL_t = log(1 + z_t⁺)`

Buyout and VC share this factor set but with different betas.

Structural priors:

- **Buyout PE**
  - β_SC ≈ 1.5
  - β_CS ≈ 0.8
  - β_INNOV ≈ 0.1
  - β_TAIL ≈ 1.2

- **Venture Capital**
  - β_SC ≈ 1.2
  - β_CS ≈ 0.4
  - β_INNOV ≈ 1.1
  - β_TAIL ≈ 2.0

These priors come from the broader unified model and reflect leverage, credit sensitivity,
innovation exposure, and downside behavior for typical Buyout and VC universes.

## 4. Fund-Specific Overlays from HLPAF Fact Sheet

From the August 2025 fact sheet, we use the following portfolio composition: fileciteturn1file0L80-L118

### 4.1 Strategy Mix

- Buyout: 79%
- Growth: 11%
- Venture: 7%
- Credit: 3%

A reasonable mapping into Buyout vs VC in our factor system is:

- Treat **Growth** as a blend of Buyout and VC (e.g. 70% Buyout / 30% VC).
- Treat **Credit** as primarily Buyout-like risk (senior in capital structure but still linked to the same companies).

One pragmatic mapping:

- Effective Buyout weight w_BO ≈ 0.79 + 0.11×0.7 + 0.03×0.8
- Effective VC weight w_VC ≈ 0.07 + 0.11×0.3 + 0.03×0.2

This yields w_BO &gt; w_VC, consistent with a Buyout-dominated, growth-tilted private assets fund.

Using the `strategy_mix_overlay` from the code base, we blend Buyout and VC structural betas
into a **base HLPAF strategy beta vector**.

### 4.2 Sector Overlay

Sector weights: fileciteturn1file0L80-L86

- Information Technology: 29%
- Industrials: 20%
- Health Care: 17%
- Financials: 13%
- Consumer Discretionary: 9%
- Communication Services: 3%
- Consumer Staples: 4%
- Materials: 2%
- Real Estate: 2%
- Utilities: 1%

The **29% tech weight** is materially above a generic private-equity baseline (say 15–20%),
and suggests a non-trivial **innovation tilt** even in &quot;Buyout&quot; deals.
We use this tech share in `sector_overlay` to modestly increase the **INNOV** and **TAIL**
betas for HLPAF.

### 4.3 Geography Overlay

Geographic mix: fileciteturn1file0L80-L86

- North America: 71%
- Europe: 22%
- Asia-Pacific: 3%
- Rest of World: 4%

We feed these into `geography_overlay`, which modestly increases SC beta for a
North-America-heavy portfolio (reflecting somewhat higher cyclicality vs a fully global mix).

### 4.4 Investment Type Overlay

Investment types: fileciteturn1file0L80-L118

- Direct Co-Investments: 49%
- Single-Asset Secondary (GP-led): 12%
- Structured Secondary (GP-led): 12%
- Multi-Asset Secondary (GP-led): 11%
- Diversified Secondary (LP-led): 16%

This mix implies a **high degree of deal and GP concentration** (co-investments and GP-led
secondaries), with a smaller ballast of diversified LP-led secondaries.

We map this into a **concentration level** (e.g. ~0.7 on a 0–1 scale) and use
`investment_type_overlay` to scale up **TAIL** beta accordingly.

### 4.5 Resulting HLPAF Factor Betas

Combining:

1. Strategy mix overlay (Buyout/VC blend),
2. Sector overlay (29% tech),
3. Geography overlay (71% NA),
4. Investment type overlay (high concentration),

we obtain an HLPAF-specific beta vector:

- β_SC^HL ≈ *greater than pure Buyout* (levered small-cap tilt, NA-heavy),
- β_CS^HL ≈ *close to Buyout*, slightly adjusted,
- β_INNOV^HL ≈ *meaningfully above pure Buyout*, below VC,
- β_TAIL^HL ≈ *above pure Buyout*, below pure VC but still high.

Exact numerical values depend on the scaling choices in the overlays, which are
transparent and tunable in the accompanying notebook.

## 5. Comparison to S&amp;P 500 in the Same Factor Space

We map the **S&amp;P 500** (via SPY or index total returns) into the same factor space by:

1. Building SC, CS, INNOV, and TAIL factors from public data (see `03_real_data_factors.ipynb`).
2. Running a regression of S&amp;P 500 returns on the four factors.
3. Obtaining β_SC^SP, β_CS^SP, β_INNOV^SP, β_TAIL^SP.

Typically, we expect:

- β_SC^SP &lt; 1 (S&amp;P 500 is large-cap, not small-cap).
- β_CS^SP modest but non-zero (equities are sensitive to credit conditions).
- β_INNOV^SP positive but smaller than HLPAF, which combines buyout and growth tech exposure.
- β_TAIL^SP significant (public equity drawdowns), but HLPAF’s β_TAIL^HL still high due to leverage and concentrated GP-led exposure.

Using Monte Carlo in the notebook, we then simulate:

- many joint paths of factors (SC, CS, INNOV, TAIL),
- implied S&amp;P 500 returns using β^SP,
- implied HLPAF returns using β^HL (with idiosyncratic noise calibrated to a realistic level).

We compute:

- distribution of cumulative returns,
- VaR and CVaR over relevant horizons (e.g. 1-year, 3-year),
- tail loss percentiles.

### High-Level Conclusion

- The **reported HLPAF returns** (5–6% annualized volatility, max drawdown ≈ –1.7%) are
  **much smoother** than both S&amp;P 500 behavior and what our structural factor model implies.
- Under the structural model with HLPAF-specific overlays, the Fund’s **true economic risk**
  is likely **broadly comparable to, or somewhat higher than, public equity risk**:
  - higher exposure to small-cap and credit spreads,
  - elevated tail risk due to leverage and concentrated GP-led structures,
  - additional innovation exposure vs a broad large-cap equity index.
- Therefore, in a **systemic crisis**, HLPAF should be modeled as experiencing
  **drawdowns of similar order of magnitude as equities** (if not larger),
  even though its reported appraisal-based NAV path may show mild declines.

## 6. Practical Recommendations

1. **Do not use** the reported HLPAF monthly return series as the primary input for
   volatility or drawdown estimates.
2. Use the **structural factor model with HLPAF overlays** for:
   - covariance estimation,
   - scenario analysis,
   - Monte Carlo-based VaR / CVaR.
3. Use HLPAF’s reported returns only for:
   - sanity-checking long-run average performance vs expectations,
   - calibrating the level (mean) of the return distribution,
   - not for estimating volatility or tail risk.
4. When integrating into an asset-allocation or **Black–Litterman** framework, treat HLPAF as:
   - a private asset with **equity-like or higher downside risk**,
   - not as a low-volatility diversifier similar to investment-grade credit or core real estate.
