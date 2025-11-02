# pip install pandas numpy statsmodels yfinance matplotlib

import pandas as pd
import numpy as np
import statsmodels.api as sm
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

# ============================================================
# 0) CONFIG
# ============================================================
ANCHOR_MONTH = "2025-08"     # align to this month (inclusive) if using a benchmark
TARGET_VOL_MULT = 1.5        # de-smoothed PE vol target relative to benchmark vol
USE_YFINANCE_BENCH = True    # set False to skip downloading benchmark
BENCH_TICKER = "ACWI"        # or "URTH"
BENCH_START = "2020-08-01"
BENCH_END   = "2025-09-01"
MAX_LAG_MARKET = 6           # lags for market-anchored de-smoothing
SHOW_PLOTS = True            # set False if running headless

# ============================================================
# 1) INPUT: Provide a PRICE series for the appraisal-smoothed asset (PE)
#    Example below uses your Class I MONTHLY RETURNS to build a pseudo-price
#    For real appraisal smoothing analysis, REPLACE THIS with true appraisal PRICES
#    (e.g., monthly NAVs) if you have them.
# ============================================================

# Example: starting from reported MONTHLY RETURNS (%), we synthesize a price index
class_i_returns_pct = {
  "2020-09": 0.11, "2020-10": 3.72, "2020-11": 1.52, "2020-12": 2.20,
  "2021-01": 0.00, "2021-02": 0.27, "2021-03": 2.25, "2021-04": 1.28, "2021-05": 1.71, "2021-06": 4.92, "2021-07": 0.17, "2021-08": 2.73, "2021-09": 0.14, "2021-10": 5.18, "2021-11": 0.09, "2021-12": 2.19,
  "2022-01": -1.56, "2022-02": 0.44, "2022-03": 1.67, "2022-04": -1.30, "2022-05": 2.34, "2022-06": -0.68, "2022-07": 4.80, "2022-08": 1.66, "2022-09": -0.74, "2022-10": 4.00, "2022-11": 3.56, "2022-12": 1.20,
  "2023-01": 2.53, "2023-02": 0.12, "2023-03": 1.25, "2023-04": -1.49, "2023-05": 0.20, "2023-06": 2.95, "2023-07": 0.60, "2023-08": -0.79, "2023-09": 1.13, "2023-10": 0.06, "2023-11": 2.25, "2023-12": 3.04,
  "2024-01": 0.66, "2024-02": 0.96, "2024-03": 0.57, "2024-04": -0.90, "2024-05": 0.94, "2024-06": 2.24, "2024-07": 0.33, "2024-08": 1.44, "2024-09": 1.82, "2024-10": -0.53, "2024-11": 2.37, "2024-12": -0.34,
  "2025-01": 1.64, "2025-02": 0.82, "2025-03": 1.29, "2025-04": 1.35, "2025-05": 2.63, "2025-06": 2.59, "2025-07": 0.37, "2025-08": -0.67
}
ci_ret = pd.Series(class_i_returns_pct, dtype=float)
ci_ret.index = pd.to_datetime(ci_ret.index).to_period("M")

# Build a *price* index from returns (100 starting level) — REPLACE with real NAVs if you have them
ci_price = (1 + ci_ret/100.0).cumprod() * 100.0
ci_price.name = "ci_price"

# ============================================================
# 2) BASIC DIAGNOSTICS: where is the serial correlation?
# ============================================================
def adf_pvalue(x, name="series"):
    x = pd.Series(x).dropna()
    try:
        return adfuller(x)[1]
    except Exception:
        return np.nan

def ac1(x):
    x = pd.Series(x).dropna()
    if len(x) < 2: return np.nan
    return x.autocorr(lag=1)

print("\n=== Stationarity (ADF p-values) ===")
print(f"ADF p-value (prices):  {adf_pvalue(ci_price, 'ci_price'):.4f}")
print(f"ADF p-value (returns): {adf_pvalue(ci_ret,   'ci_ret'):.4f}")

print("\n=== Autocorrelation at lag 1 (AC1) ===")
print(f"AC1(prices):  {ac1(ci_price):.3f}")
print(f"AC1(returns): {ac1(ci_ret):.3f}")

if SHOW_PLOTS:
    # ACF/PACF for prices and returns
    fig1 = plt.figure()
    plot_acf(ci_price.astype(float), lags=12)
    plt.title("ACF: Prices (appraisal-based)")

    fig2 = plt.figure()
    plot_acf(ci_ret.astype(float), lags=12)
    plt.title("ACF: Returns")

    fig3 = plt.figure()
    plot_pacf(ci_ret.astype(float), lags=12, method="ywm")
    plt.title("PACF: Returns")
    plt.show()

# ============================================================
# 3) AR(returns) and ARIMA(prices)
# ============================================================
# AR(1) on returns: r_t = a + rho*r_{t-1} + e_t
Z = pd.DataFrame({"r": ci_ret, "lag1": ci_ret.shift(1)}).dropna()
X = sm.add_constant(Z["lag1"])
ar1 = sm.OLS(Z["r"], X).fit()
print("\n=== AR(1) on returns ===")
print(f"alpha={ar1.params['const']:.3f} (p={ar1.pvalues['const']:.3f}) "
      f"rho={ar1.params['lag1']:.3f} (p={ar1.pvalues['lag1']:.3f})  R2={ar1.rsquared:.3f}")

# ARIMA on prices (d=1 → model returns with ARMA terms)
best = None
for p in range(0,3):
    for q in range(0,3):
        try:
            m = sm.tsa.arima.model.ARIMA(ci_price.astype(float), order=(p,1,q)).fit()
            cand = (m.aic, p, q, m)
            best = cand if (best is None or cand[0] < best[0]) else best
        except Exception:
            pass

if best:
    aic, p, q, m = best
    print(f"\n=== Best ARIMA on prices (by AIC) ===")
    print(f"ARIMA({p},1,{q})  AIC={aic:.2f}")
else:
    print("\nARIMA search failed (insufficient data or singular fit).")

# ============================================================
# 4) DE-SMOOTHING
#    A) AR(1) inverse (if rho>0 and significant)
#    B) Market-anchored (sum-lag beta moved to t) — preferred for appraisal smoothing
# ============================================================

# A) AR(1) inverse de-smoothing (only sensible if rho>0: positive appraisal smoothing)
ci_unsm_ar = None
rho = float(ar1.params["lag1"])
rho_p = float(ar1.pvalues["lag1"])
if (rho > 0.0) and (rho_p < 0.10) and (abs(1-rho) > 1e-6):
    ci_unsm_ar = (ci_ret - rho*ci_ret.shift(1)) / (1 - rho)
    ci_unsm_ar = ci_unsm_ar.dropna()
    print("\nDe-smoothing via AR(1) inverse applied (rho>0 & significant).")
else:
    print("\nAR(1) inverse NOT applied (rho<=0 or insignificant) — using market-anchored method if benchmark available.")

# Optional benchmark for market-anchored method
mx = None
if USE_YFINANCE_BENCH:
    df = yf.download(BENCH_TICKER, start=BENCH_START, end=BENCH_END, progress=False, group_by="ticker")
    if df is not None and not df.empty:
        # Handle multiindex/single index
        if isinstance(df.columns, pd.MultiIndex):
            try:
                adj = df[BENCH_TICKER]["Adj Close"]
            except Exception:
                adj = df.xs("Adj Close", axis=1, level=-1)
                if isinstance(adj, pd.DataFrame) and BENCH_TICKER in adj.columns:
                    adj = adj[BENCH_TICKER]
        else:
            adj = df["Adj Close"]
        mx = adj.resample("M").last().pct_change() * 100.0
        mx = mx.to_period("M")
        # align contiguous window to ANCHOR_MONTH
        anchor = pd.Period(ANCHOR_MONTH, freq="M")
        common = ci_ret.index.intersection(mx.index)
        common = common[common <= anchor]
        if len(common):
            contig = pd.period_range(common.min(), anchor, freq="M")
            ci_ret = ci_ret.reindex(contig)
            mx = mx.reindex(contig)
            # trim leading NaNs
            start = max(ci_ret.first_valid_index(), mx.first_valid_index())
            ci_ret = ci_ret[ci_ret.index >= start]
            mx = mx[mx.index >= start]
            # final
            window = ci_ret.index.intersection(mx.index)
            ci_ret = ci_ret.reindex(window)
            mx = mx.reindex(window)
            if bool(ci_ret.isna().any()) or bool(mx.isna().any()):
                print("Warning: non-contiguous after trim; check data.")
        else:
            print("No common months with benchmark; market-anchored method will be skipped.")
    else:
        print("Benchmark download failed; market-anchored method will be skipped.")

# B) Market-anchored de-smoothing (preferred) — requires mx
ci_unsm_mkt = None
if mx is not None and len(mx) >= 12:
    # Regress ci_ret on current + lagged mx, then move total beta to contemporaneous month
    df2 = pd.DataFrame({"ci": ci_ret, "mx0": mx})
    for k in range(1, MAX_LAG_MARKET+1):
        df2[f"mx{k}"] = mx.shift(k)
    Z = df2.dropna()
    X = sm.add_constant(Z[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]])
    y = Z["ci"]
    ols = sm.OLS(y, X).fit()
    beta_sum = float(ols.params[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]].sum())
    alpha_m = float(ols.params["const"])
    # de-smoothed (keep idiosyncratic residuals, shift market impact to t)
    resid = y - ols.fittedvalues
    # optional: whiten residuals lightly
    rho_e = resid.autocorr(lag=1)
    if np.isfinite(rho_e) and abs(rho_e) > 0.1 and abs(1-rho_e) > 1e-6:
        resid_star = (resid - rho_e*resid.shift(1)) / (1 - rho_e)
    else:
        resid_star = resid
    ci_unsm_mkt = (alpha_m + beta_sum * Z["mx"]) + resid_star
    ci_unsm_mkt = ci_unsm_mkt.dropna()

    # Scale to exceed benchmark volatility
    common2 = ci_unsm_mkt.index.intersection(mx.index)
    vol_mx = mx.loc[common2].std()
    vol_ci_star = ci_unsm_mkt.loc[common2].std()
    scale = (TARGET_VOL_MULT * vol_mx) / vol_ci_star if vol_ci_star > 0 else 1.0
    ci_unsm_mkt_scaled = ci_unsm_mkt * scale

    # Report
    def ann_vol(x): return x.std() * np.sqrt(12)
    def beta_vs(y, x):
        aligned = pd.concat([y, x], axis=1).dropna()
        aligned.columns = ["y","x"]
        res = sm.OLS(aligned["y"], sm.add_constant(aligned["x"])).fit()
        return float(res.params["x"]), float(res.pvalues["x"])

    b_raw, p_raw = beta_vs(ci_ret, mx)
    b_star, p_star = beta_vs(ci_unsm_mkt, mx)
    b_star_s, p_star_s = beta_vs(ci_unsm_mkt_scaled, mx)

    print("\n=== Market-anchored de-smoothing (with scaling) ===")
    print(f"Sum of betas on mx lags: {beta_sum:.3f}")
    print(f"Vols (monthly %, annualized in parentheses):")
    print(f"  MX           : {mx.std():.2f}%  ({ann_vol(mx):.2f}%)")
    print(f"  CI (raw)     : {ci_ret.std():.2f}%  ({ann_vol(ci_ret):.2f}%)")
    print(f"  CI* (unsm)   : {ci_unsm_mkt.std():.2f}%  ({ann_vol(ci_unsm_mkt):.2f}%)")
    print(f"  CI*s (scaled): {ci_unsm_mkt_scaled.std():.2f}%  ({ann_vol(ci_unsm_mkt_scaled):.2f}%)  [target {TARGET_VOL_MULT:.2f}× MX]")

    print("\nBetas vs MX:")
    print(f"  beta(CI, MX)       = {b_raw:.3f} (p={p_raw:.3f})")
    print(f"  beta(CI*, MX)      = {b_star:.3f} (p={p_star:.3f})")
    print(f"  beta(CI*s, MX)     = {b_star_s:.3f} (p={p_star_s:.3f})")

    if SHOW_PLOTS:
        plt.figure()
        ci_ret.plot(label="CI (raw)")
        ci_unsm_mkt.plot(label="CI* (unsm, mkt-anchored)")
        ci_unsm_mkt_scaled.plot(label="CI*s (scaled)")
        plt.legend(); plt.title("CI returns: raw vs de-smoothed"); plt.show()

elif ci_unsm_ar is not None:
    # If we applied AR(1) inverse, summarize it
    def ann_vol(x): return x.std() * np.sqrt(12)
    print("\n=== AR(1) inverse de-smoothing summary ===")
    print(f"Vol (raw): {ci_ret.std():.2f}%  ({ann_vol(ci_ret):.2f}%)")
    print(f"Vol (unsm): {ci_unsm_ar.std():.2f}%  ({ann_vol(ci_unsm_ar):.2f}%)")
    print(f"AC1(raw)={ci_ret.autocorr(1):.3f}  AC1(unsm)={ci_unsm_ar.autocorr(1):.3f}")
else:
    print("\nNo de-smoothing applied (no suitable rho and no benchmark). Provide a benchmark or true NAV prices.")