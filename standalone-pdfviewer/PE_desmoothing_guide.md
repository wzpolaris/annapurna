
# Private-Equity Return De-Smoothing — Methods, Formulas, and How-To Guide

This guide documents the approaches implemented in the accompanying Python scripts for **de-smoothing** appraisal-based return series (e.g., private equity funds). It includes **diagnostics**, two complementary **de-smoothing models**, and options for **volatility targeting**. All formulas below use LaTeX.

---

## 0) Notation and Units

- We work with **monthly returns in percent points**:  
  `1.25` means **+1.25%** in that month.  
- Let:
  - \( r^{CI}_t \): reported PE monthly return (appraisal-based).  
  - \( r^{MX}_t \): benchmark monthly return (e.g., MSCI World proxy like ACWI/URTH).  
  - \( \bar r^{MX} \): sample mean of \( r^{MX}_t \).  
  - \( \mu_M \): **assumed** market expected return (monthly); we typically start from an annual value, e.g. \(6\%\), and convert to monthly via
    \[
    \mu_{M,\text{monthly}} \;=\; (1+\mu_{M,\text{annual}})^{1/12} - 1.
    \]
  - \( \sigma_M \): **assumed** market volatility (monthly); conversion from annual uses
    \[
    \sigma_{M,\text{monthly}} \;=\; \frac{\sigma_{M,\text{annual}}}{\sqrt{12}}.
    \]
  - All \(\mu\) and \(\sigma\) above are in **percent points** when used in code.

---

## 1) Diagnostics — Why De-Smooth?

### 1.1 Stationarity (ADF)
- Prices (cumulated from returns) should be **non-stationary**; returns should be **stationary**.  
- We verify using the Augmented Dickey-Fuller test:
  - High p-value for prices → random-walk-like level.  
  - Low p-value for returns → stationary return process.

### 1.2 Autocorrelation (ACF/PACF & AR(1))
We typically fit an AR(1) to monthly returns:
\[
r_t \;=\; \alpha \;+\; \rho\, r_{t-1} \;+\; \varepsilon_t.
\]
- **Smoothing** shows up as **positive** \(\rho\).  
- In practice for the provided dataset, \(\rho\) is slightly **negative**, suggesting mean reversion rather than appraisal smoothing in returns.

**Interpretation**: de-smoothing by AR-inversion is only justified when \(\rho>0\) and is material. Otherwise, focus on **timing/lag** (market-anchored) or a **structural risk** view.

---

## 2) Market-Anchored De-Smoothing (Empirical / Timing Model)

**Purpose**: Appraisals often lag public markets. We estimate how much the fund loads on **current and lagged** market returns, then **re-time** the exposure to be contemporaneous.

### 2.1 Regression with lags
Fit:
\[
r^{CI}_t \;=\; \alpha \;+\; \sum_{k=0}^{K} \beta_k \, r^{MX}_{t-k} \;+\; \varepsilon_t.
\]

### 2.2 Re-timing (“unsmoothing”)
Move the lagged exposure to the current month:
\[
r^{CI*}_t \;=\; \alpha \;+\; \left(\sum_{k=0}^{K} \beta_k\right) r^{MX}_t \;+\; \varepsilon^{*}_t.
\]
- \(\varepsilon^{*}_t\) may be lightly **whitened** from \(\varepsilon_t\) if residual AC(1) is material:
  \[
  \varepsilon^{*}_t \;=\; \frac{\varepsilon_t - \varphi \,\varepsilon_{t-1}}{1-\varphi},\quad \varphi \approx \text{AC1}(\varepsilon).
  \]

### 2.3 Mean-Preserving Volatility Scaling (`CI*s`)
Scale deviations around the mean to reach a target multiple of benchmark volatility **without changing the mean**:
\[
r^{CI*s}_t \;=\; \bar r^{CI*} \;+\; \lambda \left(r^{CI*}_t - \bar r^{CI*}\right), \qquad 
\lambda \;=\; \frac{\text{target\_mult}\cdot \sigma(r^{MX})}{\sigma(r^{CI*})}.
\]

**Interpretation**:
- `CI*` is the **contemporaneous** version of the reported series.
- `CI*s` preserves the **average return** but matches a **risk budget** (e.g., \(1.5\times\) market vol).

---

## 3) Structural Models — Economic Risk View

Rather than only correcting timing, these models assume PE returns reflect a **systematic market component** plus **idiosyncratic noise**, then choose parameters to meet your **risk** and **beta** beliefs.

We present two versions:

### 3.1 Hybrid Leverage Structural Model
Assume the systematic piece is **LEVERAGE × market**. We separate **systematic** and **idiosyncratic** parts:

- **Systematic component** (centered so drift comes from the assumption):
  \[
  r^{sys}_t \;=\; L\,(r^{MX}_t - \bar r^{MX}) \;+\; L\,\mu_M,
  \]
  where \(L\) is the **leverage multiple** (e.g., 2× or 3×).
- **Idiosyncratic component**: reuse residuals \(\varepsilon^{*}_t\) from the market-anchored fit.

**Hybrid total volatility targeting**: pick a **target total volatility** so that
\[
\sigma_{\text{target}} \;\ge\; \max\!\Big( L\cdot \sigma_M,\;\; \text{target\_mult}\cdot \sigma(r^{MX}) \Big).
\]
Then scale residuals to fill the gap:
\[
r^{struct}_t \;=\; r^{sys}_t \;+\; k\,\varepsilon^{*}_t,\qquad
k \;=\; \sqrt{\frac{\sigma_{\text{target}}^2 \;-\; \sigma^2(r^{sys})}{\sigma^2(\varepsilon^{*})}}\;\;\; (\text{clipped at }0).
\]

**Notes**:
- If you want **realized beta \(\approx L\)** on the sample, you can enforce the slope on \(r^{MX}\) to be \(L\) by construction (adjust intercept accordingly).
- This model interprets the steady “1.6%/mo” as part of a **levered market drift**.

### 3.2 CAPM-Based Structural Model
Here we **estimate the observed beta** on the **de-lagged** series `CI*` via a CAPM regression, then apply your leverage to that beta:

1) CAPM on `CI*`:
\[
r^{CI*}_t \;=\; \alpha \;+\; \hat\beta\; r^{MX}_t \;+\; \varepsilon_t.
\]

2) Set the **systematic beta** after leverage:
\[
\beta_{\text{sys}} \;=\; L \cdot \hat\beta.
\]

3) Build the systematic component (again, centered for drift control):
\[
r^{sys}_t \;=\; \beta_{\text{sys}}\,(r^{MX}_t - \bar r^{MX}) \;+\; \beta_{\text{sys}} \,\mu_M.
\]

4) Scale residuals from the market-anchored fit (aligned to this window) to hit the **same hybrid volatility target**:
\[
\sigma_{\text{target}} \;\ge\; \max\!\Big( |\beta_{\text{sys}}| \cdot \sigma_M,\;\; \text{target\_mult}\cdot \sigma(r^{MX}) \Big),
\]
\[
r^{struct,\,CAPM}_t \;=\; r^{sys}_t \;+\; k\,\varepsilon^{*}_t, \qquad
k \;=\; \sqrt{\frac{\sigma_{\text{target}}^2 \;-\; \sigma^2(r^{sys})}{\sigma^2(\varepsilon^{*})}}.
\]

**Interpretation**:
- The **systematic loading** reflects **observed beta after de-lagging**, scaled by your leverage belief.
- This is often preferable to assuming beta equals the leverage multiple, because it anchors on the **empirical contemporaneous sensitivity**.

---

## 4) VOL Targeting and the `TARGET_MULT` Parameter

- `TARGET_MULT` ties total risk to the **realized** benchmark volatility:  
  \[
  \sigma_{\text{multiple}} \;=\; \text{target\_mult} \cdot \sigma(r^{MX}).
  \]
- The **hybrid target** takes the **maximum** of the **assumed leverage-implied** volatility and the **multiple target**:
  \[
  \sigma_{\text{target}} \;=\; \max\!\big(\sigma_{\text{leverage}},\;\sigma_{\text{multiple}}\big).
  \]
- This ensures your structural series is **at least** as volatile as what your leverage physics imply **and** not below the chosen **market multiple**.

---

## 5) How to Interpret Outputs

### 5.1 Table Columns (from the script)
- **mean (pp/mo)**: average monthly return in percent points.  
- **stdev (mo %) / (ann %)**: monthly and annualized standard deviation (percent).  
- **beta vs MX**: CAPM beta vs realized market over the aligned window.  
- **alpha (pp/mo)**: CAPM intercept (conditional on market); note this mixes drift and model specification — use **mean** for drift intuition.  
- **AC1**: lag-1 autocorrelation of the monthly returns.

### 5.2 Comparing Series
- **CI raw**: as reported; often too smooth.  
- **CI\***: contemporaneous timing; removes lag bias if present.  
- **CI\*s**: same mean as CI\*, with volatility scaled to a chosen multiple.  
- **Structural HYBRID**: systematic exposure based on **LEVERAGE**; residuals scaled to a hybrid target. Optionally enforce realized \(\beta\approx L\).  
- **Structural CAPM**: systematic exposure based on \(\beta_{\text{sys}}=L\cdot\hat\beta\) where \(\hat\beta\) is **measured on CI\***. Residuals scaled to hybrid target.

**Which to use?**
- Use **Market-Anchored** when you believe the main issue is **timing lag**.  
- Use **Structural HYBRID** when you want PE to behave like a levered market exposure with additional idiosyncratic risk.  
- Use **Structural CAPM** when you want the **systematic loading** to reflect the **observed (de-lagged) beta**, then **apply leverage**.

---

## 6) Practical Tips

- Always align series on a **contiguous window** ending at a known **anchor month** to avoid survivorship and alignment artifacts.  
- If AR(1) on returns shows **\(\rho>0\)** and significant, consider **AR-inverse de-smoothing**. If \(\rho\le 0\) or small, focus on **market-anchored** or **structural** methods.  
- When **scaling**, decide whether to **preserve the mean** (`CI*s`) or **rebuild the mean from assumptions** (structural models).  
- For **beta interpretation**, rely on the **CAPM slope** (vs realized market) over the aligned window, not just the constructed leverage.

---

## 7) Example Configuration Choices

- **Empirical focus** (timing fix): `MAX_LAG_MARKET=6`, `TARGET_MULT=1.5`, use `CI*` and `CI*s`.  
- **Structural risk view**: set `LEVERAGE=2.0` or `3.0`, `ANN_MU=0.06`, `ANN_SIGMA=0.20`, `TARGET_MULT=1.5`. Compare **HYBRID** vs **CAPM** structural outputs.  
- **Force β**: set `ENFORCE_REALIZED_BETA=True` in **HYBRID** to match realized beta ≈ \(L\).

---

## 8) Caveats

- Yahoo’s **auto-adjust** approximates total return; not perfect for all funds or geographies.  
- CAPM is a single-factor model; in PE, other drivers (size, quality, sector tilts, liquidity) may matter.  
- De-smoothing is **model-dependent**; report sensitivity to parameter choices (\(L\), \(\mu_M\), \(\sigma_M\), `TARGET_MULT`).

---

## 9) Minimal “How-To” Checklist

1. **Load** monthly PE returns (percent points) and **download** benchmark prices.  
2. Convert prices to monthly returns; align on a **contiguous period**.  
3. Run **diagnostics** (ADF, AC1, AR(1)).  
4. Build **CI\*** via the **lag regression** and re-timing.  
5. Optionally **scale** `CI*` to `CI*s` (mean-preserving) with a chosen `TARGET_MULT`.  
6. **Structural HYBRID**: make \(r^{sys}_t\) using \(L\), add residuals scaled to the **hybrid target**.  
7. **Structural CAPM**: estimate \(\hat\beta\) from `CI*`, set \(\beta_{sys}=L\cdot\hat\beta\), add scaled residuals to the **hybrid target**.  
8. Compare **mean, vol (mo/ann), beta, AC1** across series; choose the representation that fits your investment rationale.

---

*Prepared for reproducible workflows alongside the companion Python scripts. Adjust parameters to fit your investment beliefs and data specifics.*
