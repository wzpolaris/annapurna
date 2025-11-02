
# Private Equity De-Smoothing and CAPM Structural Model Summary

## 1. Appraisal Smoothing Evidence

| Metric | Observation | Interpretation |
|---------|--------------|----------------|
| **ADF (prices)** | 0.9445 | Prices are **non-stationary** (typical for cumulative appraisal values). |
| **ADF (returns)** | 0.0000 | Returns are **stationary**—good for modeling. |
| **AC1 (prices)** | 0.997 | Price changes are highly persistent; appraisal values evolve almost deterministically. |
| **AC1 (returns)** | −0.228 | Mild mean-reversion once converted to returns, consistent with lagged appraisals. |

---

## 2. Market-Anchored De-Smoothing

The regression of CI on **lagged MSCI ACWI returns** found a small negative lag-sum (−0.04), meaning the reported returns slightly *lag* market moves.  
De-smoothing removes that lag, producing **CI\\*** with:

- Volatility falling to 1.06%/mo (3.7% annualized)
- Near-zero autocorrelation (AC1 ≈ 0)

Scaling by 1.5× market volatility (“CI\\*s”) raises risk to match a plausible PE risk level while preserving the mean return.

---

## 3. CAPM Structural Model (+α)

### Systematic Component

\[
\beta_{\text{sys}} = L \times \hat\beta = 2.0 \times (-0.04) = -0.08
\]

### Expected Market Return

\[
E[r_M] = 0.487\%\text{/mo}
\]
so:
\[
\beta_{\text{sys}} \times E[r_M] = -0.039\%\text{/mo}
\]

### Observed Mean of CI*

\[
\bar r^{CI*} = 1.249\%\text{/mo}
\]

### Private Equity Excess Return

\[
\alpha_i = \bar r^{CI*} - \beta_{\text{sys}}E[r_M]
           = 1.249 - (-0.039)
           = 1.288\%\text{/mo}
\]

This represents the **“PE premium”** unexplained by systematic risk.

---

## 4. Volatility Targeting

- Assumed market vol (monthly): 5.77%
- Target total vol: 6.42%
- Residual scale factor \(k_\varepsilon = 6.12\) boosts idiosyncratic noise to reach the risk target without changing mean or beta.

---

## 5. Summary Comparison

| Series | Mean (pp/mo) | Ann. Vol | Beta | AC1 | Comment |
|--------|---------------|-----------|-------|------|----------|
| **CI raw** | 1.26 | 5.4% | 0.22 | −0.23 | Appraised; smoothed and lagged |
| **CI\\*** | 1.25 | 3.7% | −0.04 | ≈0 | De-smoothed, low vol |
| **CI\\*s** | 1.25 | 22.2% | −0.24 | ≈0 | Scaled to plausible PE risk |
| **CAPM+ structural** | 1.25 | 22.2% | −0.08 | ≈0 | Matches observed mean, decomposes into β×market + α_PE |

---

## 6. Interpretation

- The **reported (CI)** series displays extreme smoothing; returns are nearly deterministic.  
- **De-smoothing (CI\\*)** restores stationarity and removes autocorrelation.  
- **Scaled (CI\\*s)** gives a risk profile comparable to market multiples.  
- The **CAPM+ structural** model enforces:

\[
E[r_{PE}] = \alpha_i + \beta_{\text{sys}}E[r_M]
\]

reproducing the **observed mean** while separating:

- **Systematic exposure (−0.08β)** → negligible  
- **Private equity excess α = 1.29 pp/mo** → dominant source of expected return

Economically, this means:

> *Observed PE performance cannot be explained by market beta; it reflects a large, idiosyncratic premium.*

---

**Model Parameters:**  
- Leverage (L): 2.0  
- Market expected return (annual): 6%  
- Market volatility (annual): 20%  
- Target volatility multiplier: 1.5×  
- Benchmark: MSCI ACWI  
