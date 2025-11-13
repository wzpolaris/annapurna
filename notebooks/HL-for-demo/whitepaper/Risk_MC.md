# Risk Analytics & Monte Carlo

The unified factor model is primarily intended for **risk analysis**. Once we have:

- Historical factor time series \( F_t = (SC_t, CS_t, INNOV_t, TAIL_t) \)
- Structural (or blended) betas \( \beta \) for each private asset or fund

we can simulate hypothetical return paths and compute risk measures.

## 1. Factor Covariance and Distributions

From historical factor data, we estimate:

- mean vector \( \mu_F \)
- covariance matrix \( \Sigma_F \)

We can then simulate factor returns in several ways:

1. **Multivariate normal**:
   \[
   F^{(sim)} \sim \mathcal{N}(\mu_F, \Sigma_F).
   \]
2. **Multivariate t** (heavier tails).
3. **Bootstrap or block‑bootstrap**:
   - resample historical months or blocks of months,
   - preserves empirical skew and kurtosis,
   - preserves cross‑factor dependence during crises.

## 2. Mapping to Private Returns

For a given private asset (Buyout or VC) with beta vector \( \beta \):

\[
r^{Priv,(sim)}_t = \beta^\top F^{(sim)}_t + \varepsilon^{(sim)}_t,
\]

where \( \varepsilon^{(sim)}_t \) is idiosyncratic noise (often modeled as normal with
volatility chosen to match residual variance).

By simulating many paths, we obtain an empirical distribution of:

- cumulative returns,
- drawdowns,
- annualized volatility,
- tail losses.

## 3. Risk Measures

From the simulated distribution we can compute:

- **Value at Risk (VaR)** at different horizons,
- **Conditional VaR (CVaR)** / expected shortfall,
- Tail percentiles (e.g. 1%, 5% worst outcomes),
- Relative risk vs a public equity benchmark.

The same framework can be applied:

- at the **fund level**, using fund‑specific betas,
- at the **portfolio level**, combining factor exposures across funds and strategies.

## 4. Comparison to Public Equity

Because SC, CS, INNOV, and TAIL are also relevant for public equity, we can:

- build a comparable factor representation for a public‑equity portfolio, and
- compare Buyout / VC risk metrics versus public equity on a **like‑for‑like factor basis**.

This is particularly useful for investment committees evaluating how much additional
tail risk is introduced by adding private strategies to a public portfolio.
