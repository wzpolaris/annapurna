# pip install yfinance statsmodels pandas numpy

import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm

# -----------------------------
# 0) Config
# -----------------------------
target_mult = 1.5        # desired PE volatility multiple of MSCI (>=1)
anchor_month = "2025-08" # enforce contiguous overlap ending here

# -----------------------------
# 1) Class I monthly returns (% points)
# -----------------------------
class_i = {
  "2020-09": 0.11, "2020-10": 3.72, "2020-11": 1.52, "2020-12": 2.20,
  "2021-01": 0.00, "2021-02": 0.27, "2021-03": 2.25, "2021-04": 1.28, "2021-05": 1.71, "2021-06": 4.92, "2021-07": 0.17, "2021-08": 2.73, "2021-09": 0.14, "2021-10": 5.18, "2021-11": 0.09, "2021-12": 2.19,
  "2022-01": -1.56, "2022-02": 0.44, "2022-03": 1.67, "2022-04": -1.30, "2022-05": 2.34, "2022-06": -0.68, "2022-07": 4.80, "2022-08": 1.66, "2022-09": -0.74, "2022-10": 4.00, "2022-11": 3.56, "2022-12": 1.20,
  "2023-01": 2.53, "2023-02": 0.12, "2023-03": 1.25, "2023-04": -1.49, "2023-05": 0.20, "2023-06": 2.95, "2023-07": 0.60, "2023-08": -0.79, "2023-09": 1.13, "2023-10": 0.06, "2023-11": 2.25, "2023-12": 3.04,
  "2024-01": 0.66, "2024-02": 0.96, "2024-03": 0.57, "2024-04": -0.90, "2024-05": 0.94, "2024-06": 2.24, "2024-07": 0.33, "2024-08": 1.44, "2024-09": 1.82, "2024-10": -0.53, "2024-11": 2.37, "2024-12": -0.34,
  "2025-01": 1.64, "2025-02": 0.82, "2025-03": 1.29, "2025-04": 1.35, "2025-05": 2.63, "2025-06": 2.59, "2025-07": 0.37, "2025-08": -0.67
}

ci = pd.Series(class_i, dtype=float)
ci.index = pd.to_datetime(ci.index)
ci = ci.to_period("M")

# -----------------------------
# 2) Download MSCI proxy (ACWI -> URTH) and make monthly % returns (Adj Close)
# -----------------------------
def monthly_tr_proxy(ticker: str) -> pd.Series:
    df = yf.download(
        ticker, start="2020-08-01", end="2025-09-01",
        auto_adjust=False, progress=False, group_by="ticker"
    )
    if df is None or df.empty:
        return pd.Series(dtype=float)

    # Handle simple or MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        try:
            adj = df[ticker]["Adj Close"]
        except Exception:
            # fallback: XS last level
            if "Adj Close" in df.columns.get_level_values(-1):
                adj = df.xs("Adj Close", axis=1, level=-1)
                if isinstance(adj, pd.DataFrame) and ticker in adj.columns:
                    adj = adj[ticker]
            else:
                return pd.Series(dtype=float)
    else:
        if "Adj Close" not in df.columns:
            return pd.Series(dtype=float)
        adj = df["Adj Close"]

    # Resample to month-end and compute pct change in percent points
    mret = adj.resample("ME").last().pct_change() * 100.0
    # Ensure Series
    if isinstance(mret, pd.DataFrame):
        mret = mret.iloc[:, 0]
    return mret.to_period("M")

mx = monthly_tr_proxy("ACWI")
if mx.empty:
    mx = monthly_tr_proxy("URTH")
    if mx.empty:
        raise RuntimeError("Could not fetch ACWI or URTH. Check network/ticker.")

# -----------------------------
# 3) Align to contiguous overlap ending anchor_month
# -----------------------------
anchor = pd.Period(anchor_month, freq="M")
common = ci.index.intersection(mx.index)
common = common[common <= anchor]
if len(common) == 0:
    raise ValueError("No common months <= anchor.")

contig = pd.period_range(common.min(), anchor, freq="M")
ci = ci.reindex(contig)
mx = mx.reindex(contig)

# Trim leading NaNs to ensure contiguity
start = max(ci.first_valid_index(), mx.first_valid_index())
ci = ci[ci.index >= start]
mx = mx[mx.index >= start]
window = ci.index.intersection(mx.index)
ci, mx = ci.reindex(window), mx.reindex(window)

if bool(ci.isna().any()) or bool(mx.isna().any()):
    raise ValueError("Non-contiguous data after trimming; found NaNs.")

print(f"Contiguous window: {window[0]} → {window[-1]}  (n={len(window)})")

# -----------------------------
# 4) Estimate smoothing via AR(1) on ci
#     r_t = alpha + rho * r_{t-1} + eps_t
# -----------------------------
z = pd.DataFrame({"r": ci, "r_lag1": ci.shift(1)}).dropna()
X = sm.add_constant(z["r_lag1"])
ols_ar1 = sm.OLS(z["r"], X).fit()
rho = float(ols_ar1.params["r_lag1"])
alpha = float(ols_ar1.params["const"])
print(f"AR(1) on ci: alpha={alpha:.3f}, rho={rho:.3f}")

# -----------------------------
# 5) De-smooth using inverse AR(1) filter:
#     r*_t = (r_t - rho * r_{t-1}) / (1 - rho)
# -----------------------------
if np.isclose(1 - rho, 0.0):
    raise ValueError("rho too close to 1; inverse filter unstable.")
ci_unsm = (ci - rho * ci.shift(1)) / (1 - rho)
ci_unsm = ci_unsm.dropna()

# -----------------------------
# 6) Rescale: enforce PE total risk > MSCI (e.g., 1.5×)
#    Use monthly std; report also annualized.
# -----------------------------
vol_ci = ci.std()
vol_mx = mx.std()
vol_unsm = ci_unsm.std()

target_vol = target_mult * vol_mx
scale = target_vol / vol_unsm if vol_unsm > 0 else 1.0
ci_unsm_scaled = ci_unsm * scale

# -----------------------------
# 7) Report stats (before vs after)
# -----------------------------
def ann_vol(x): return x.std() * np.sqrt(12)
def beta(y, x):
    aX = sm.add_constant(x.dropna())
    y2 = y.reindex_like(x).dropna()
    aX = aX.reindex(y2.index)
    if len(y2) < 5:
        return np.nan, np.nan
    res = sm.OLS(y2, aX).fit()
    return float(res.params.get(x.name, np.nan)), float(res.pvalues.get(x.name, np.nan))

# Align for comparisons
mx_aligned = mx.reindex(ci.index)
mx_aligned_unsm = mx.reindex(ci_unsm.index)
mx_aligned_unsm_s = mx.reindex(ci_unsm_scaled.index)

b_ci, p_ci = beta(ci.rename("ci"), mx_aligned.rename("mx"))
b_unsm, p_unsm = beta(ci_unsm.rename("ci_unsm"), mx_aligned_unsm.rename("mx"))
b_unsm_s, p_unsm_s = beta(ci_unsm_scaled.rename("ci_unsm_s"), mx_aligned_unsm_s.rename("mx"))

print("\n--- Volatility (monthly %, annualized in parentheses) ---")
print(f"MSCI proxy      : {vol_mx:.2f}%  ({ann_vol(mx):.2f}%)")
print(f"CI (smoothed)   : {vol_ci:.2f}%  ({ann_vol(ci):.2f}%)")
print(f"CI de-smoothed  : {vol_unsm:.2f}%  ({ann_vol(ci_unsm):.2f}%)")
print(f"CI de-sm + scaled ({target_mult:.2f}× MSCI target): {ci_unsm_scaled.std():.2f}%  ({ann_vol(ci_unsm_scaled):.2f}%)")

print("\n--- First-order autocorrelation (AC1) ---")
print(f"AC1 MSCI : {mx.autocorr(lag=1):.3f}")
print(f"AC1 CI   : {ci.autocorr(lag=1):.3f}")
print(f"AC1 CI*  : {ci_unsm.autocorr(lag=1):.3f}")
print(f"AC1 CI*s : {ci_unsm_scaled.autocorr(lag=1):.3f}")

print("\n--- Beta of CI variants vs MSCI (contemporaneous regression) ---")
print(f"beta(CI, MSCI)        = {b_ci:.3f} (p={p_ci:.3f})")
print(f"beta(CI*, MSCI)       = {b_unsm:.3f} (p={p_unsm:.3f})")
print(f"beta(CI* scaled, MSCI)= {b_unsm_s:.3f} (p={p_unsm_s:.3f})")

print("\nInterpretation:")
print("- De-smoothing should push AC1 toward ~0 and raise vol; scaling enforces PE > MSCI total risk.")
print("- Beta typically increases after de-smoothing (less appraisal lag), better reflecting true market sensitivity.")
print("- Adjust 'target_mult' to your preferred PE risk level (e.g., 1.5×–2.0× MSCI).")