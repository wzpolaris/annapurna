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

# ===================== CONFIG =====================
ANCHOR_MONTH     = "2025-08"   # align contiguous overlap ending here (inclusive)
TARGET_VOL_MULT  = 1.5         # target PE vol multiple of benchmark (>=1)
BENCH_TICKERS    = ["ACWI", "URTH"]  # try in order
BENCH_START      = "2020-08-01"
BENCH_END        = "2025-09-01"
MAX_LAG_MARKET   = 6           # lags for market-anchored de-smoothing
SHOW_PLOTS       = False

# ========== YOUR CLASS I MONTHLY RETURNS (%) ==========
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

# Build a reported (appraisal) price index from returns (base=100)
def price_from_returns(ret_series_pct: pd.Series, base: float = 100.0) -> pd.Series:
    r = (ret_series_pct / 100.0).dropna()
    px = (1.0 + r).cumprod() * base
    px.name = "price_from_returns"
    return px

ci_price = price_from_returns(ci_ret, base=100.0)
ci_price.name = "ci_price"

# ========== Robust Yahoo fetch: monthly TR proxy as Series (PeriodIndex M) ==========
def monthly_tr_proxy_robust(ticker: str, start: str, end: str) -> pd.Series:
    """
    Use auto_adjust=True, so 'Close' is back-adjusted (splits+dividends),
    providing a practical total-return proxy.
    """
    df = yf.download(
        ticker, start=start, end=end,
        auto_adjust=True, progress=False, actions=False, group_by="column"
    )
    if df is None or df.empty:
        return pd.Series(dtype=float)

    # Extract a price Series robustly
    if isinstance(df.columns, pd.MultiIndex):
        try:
            px = df.xs("Close", axis=1, level=-1)
            if isinstance(px, pd.DataFrame):
                px = px[ticker] if ticker in px.columns else px.iloc[:, 0]
        except Exception:
            px = df.select_dtypes("number").iloc[:, 0]
    else:
        px = df["Close"] if "Close" in df.columns else df.select_dtypes("number").iloc[:, 0]

    mret = px.resample("M").last().pct_change() * 100.0
    return mret.to_period("M")

# Try ACWI then URTH
mx = pd.Series(dtype=float)
for tk in BENCH_TICKERS:
    mx = monthly_tr_proxy_robust(tk, BENCH_START, BENCH_END)
    if not mx.empty:
        BENCH_USED = tk
        break
if mx.empty:
    raise RuntimeError("Benchmark download failed for ACWI/URTH.")

# ========== Align to contiguous overlap ending ANCHOR_MONTH ==========
anchor = pd.Period(ANCHOR_MONTH, freq="M")
common = ci_ret.index.intersection(mx.index)
common = common[common <= anchor]
if len(common) == 0:
    raise ValueError("No common months <= anchor.")

contig = pd.period_range(common.min(), anchor, freq="M")
ci_ret = ci_ret.reindex(contig)
mx     = mx.reindex(contig)
start  = max(ci_ret.first_valid_index(), mx.first_valid_index())
ci_ret = ci_ret[ci_ret.index >= start]
mx     = mx[mx.index >= start]
window = ci_ret.index.intersection(mx.index)
ci_ret = ci_ret.reindex(window)
mx     = mx.reindex(window)
if bool(ci_ret.isna().any()) or bool(mx.isna().any()):
    raise ValueError("Non-contiguous data after trimming; found NaNs.")

# ========== Diagnostics: ADF (prices vs returns) + ACFs ==========
def adf_pvalue(x):
    x = pd.Series(x).dropna()
    try:
        return adfuller(x)[1]
    except Exception:
        return np.nan

def ac1(x):
    x = pd.Series(x).dropna()
    return x.autocorr(1) if len(x) >= 2 else np.nan

print("\n=== Stationarity (ADF p-values) ===")
print(f"ADF p-value (prices):  {adf_pvalue(ci_price):.4f}")
print(f"ADF p-value (returns): {adf_pvalue(ci_ret):.4f}")

print("\n=== Autocorrelation at lag 1 (AC1) ===")
print(f"AC1(prices):  {ac1(ci_price):.3f}")
print(f"AC1(returns): {ac1(ci_ret):.3f}")

if SHOW_PLOTS:
    plot_acf(ci_price.astype(float), lags=12); plt.title("ACF: Prices (appraisal)"); plt.show()
    plot_acf(ci_ret.astype(float),   lags=12); plt.title("ACF: Returns"); plt.show()
    plot_pacf(ci_ret.astype(float),  lags=12, method="ywm"); plt.title("PACF: Returns"); plt.show()

# ========== AR(1) on returns; ARIMA search on prices (optional) ==========
Z = pd.DataFrame({"r": ci_ret, "lag1": ci_ret.shift(1)}).dropna()
ar1 = sm.OLS(Z["r"], sm.add_constant(Z["lag1"])).fit()
print("\n=== AR(1) on returns ===")
print(f"alpha={ar1.params['const']:.3f} (p={ar1.pvalues['const']:.3f}) "
      f"rho={ar1.params['lag1']:.3f} (p={ar1.pvalues['lag1']:.3f})  R2={ar1.rsquared:.3f}")

# Optional ARIMA(prices)
best = None
for p in range(0,3):
    for q in range(0,3):
        try:
            m = sm.tsa.arima.model.ARIMA(ci_price.astype(float), order=(p,1,q)).fit()
            if best is None or m.aic < best[0]:
                best = (m.aic, p, q)
        except Exception:
            pass
if best:
    print(f"Best ARIMA on prices by AIC: ARIMA({best[1]},1,{best[2]})  AIC={best[0]:.2f}")

# ========== De-smoothing ==========
# A) AR(1) inverse (use only if rho>0 and significant)
rho = float(ar1.params["lag1"]); rho_p = float(ar1.pvalues["lag1"])
ci_unsm_ar = None
if (rho > 0.0) and (rho_p < 0.10) and (abs(1-rho) > 1e-6):
    ci_unsm_ar = (ci_ret - rho*ci_ret.shift(1)) / (1 - rho)
    ci_unsm_ar = ci_unsm_ar.dropna()
    print("\nAR(1) inverse applied (rho>0 & significant).")
else:
    print("\nAR(1) inverse NOT applied (rho<=0 or insignificant). Using market-anchored method.")

# B) Market-anchored (preferred): sum lag betas → contemporaneous; keep residuals, lightly whiten
df2 = pd.DataFrame({"ci": ci_ret, "mx0": mx})
for k in range(1, MAX_LAG_MARKET+1):
    df2[f"mx{k}"] = mx.shift(k)
Z2 = df2.dropna()
ols = sm.OLS(Z2["ci"], sm.add_constant(Z2[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]] )).fit()
beta_sum = float(ols.params[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]].sum())
alpha_m  = float(ols.params["const"])
resid    = Z2["ci"] - ols.fittedvalues

rho_e = resid.autocorr(1)
if np.isfinite(rho_e) and abs(rho_e) > 0.1 and abs(1-rho_e) > 1e-6:
    resid_star = (resid - rho_e*resid.shift(1)) / (1 - rho_e)
else:
    resid_star = resid

ci_unsm_mkt = (alpha_m + beta_sum * Z2["mx0"]) + resid_star
ci_unsm_mkt = ci_unsm_mkt.dropna()

# Scale to exceed benchmark volatility
def ann_vol(x): return x.std() * np.sqrt(12)
def beta_vs(y, x):
    a = pd.concat([y, x], axis=1).dropna()
    a.columns = ["y","x"]
    m = sm.OLS(a["y"], sm.add_constant(a["x"])).fit()
    return float(m.params["x"]), float(m.pvalues["x"])

common2 = ci_unsm_mkt.index.intersection(mx.index)
vol_mx   = mx.loc[common2].std()
vol_star = ci_unsm_mkt.loc[common2].std()
scale    = (TARGET_VOL_MULT * vol_mx) / vol_star if vol_star > 0 else 1.0
ci_unsm_mkt_scaled = ci_unsm_mkt * scale

b_raw,  p_raw  = beta_vs(ci_ret, mx)
b_star, p_star = beta_vs(ci_unsm_mkt, mx)
b_scl,  p_scl  = beta_vs(ci_unsm_mkt_scaled, mx)

print("\n=== Market-anchored de-smoothing (with scaling) ===")
print(f"Benchmark used: {BENCH_USED}")
print(f"Sum of betas on mx lags: {beta_sum:.3f}")
print(f"Vols (monthly %, annualized):")
print(f"  MX               : {mx.std():.2f}%  ({ann_vol(mx):.2f}%)")
print(f"  CI (raw)         : {ci_ret.std():.2f}%  ({ann_vol(ci_ret):.2f}%)")
print(f"  CI* (unsm, mkt)  : {ci_unsm_mkt.std():.2f}%  ({ann_vol(ci_unsm_mkt):.2f}%)")
print(f"  CI*s (scaled {TARGET_VOL_MULT:.2f}× MX target): {ci_unsm_mkt_scaled.std():.2f}%  ({ann_vol(ci_unsm_mkt_scaled):.2f}%)")
print("Betas vs MX:")
print(f"  beta(CI, MX)       = {b_raw:.3f} (p={p_raw:.3f})")
print(f"  beta(CI*, MX)      = {b_star:.3f} (p={p_star:.3f})")
print(f"  beta(CI*s, MX)     = {b_scl:.3f} (p={p_scl:.3f})")

# ========== ADD-ON: visualize appraisal lag (prices vs de-smoothed prices) ==========
def price_from_returns_aligned(ret_series_pct: pd.Series, base: float) -> pd.Series:
    r = (ret_series_pct / 100.0).dropna()
    px = (1.0 + r).cumprod() * base
    return px

# choose de-smoothed series (prefer scaled market-anchored)
ci_unsm_choice = ci_unsm_mkt_scaled.copy()
ci_unsm_choice.name = "CI* (mkt-anchored, scaled)"

# align to reported price index span
base = float(ci_price.dropna().iloc[0])
ci_px_reported = ci_price.copy()
ci_px_unsm     = price_from_returns_aligned(ci_unsm_choice.reindex(ci_ret.index), base=base)

aligned = pd.concat([
    ci_px_reported.rename("Reported (Appraisal)"),
    ci_px_unsm.rename("De-smoothed (Instantaneous)")
], axis=1).dropna()

# Optional benchmark price (scaled to same base)
mx_px = price_from_returns_aligned(mx.reindex(aligned.index), base=aligned.iloc[0,0])
aligned["Benchmark (scaled)"] = mx_px

# Tracking error & cross-correlation
rep_ret = aligned["Reported (Appraisal)"].pct_change() * 100
uns_ret = aligned["De-smoothed (Instantaneous)"].pct_change() * 100
te = (rep_ret - uns_ret).std()

lags = range(-6, 7)
xcc = []
for k in lags:
    corr = pd.concat([rep_ret, uns_ret.shift(k)], axis=1).dropna().corr().iloc[0,1]
    xcc.append(corr)
best_k = lags[int(np.nanargmax(xcc))] if len(xcc) else 0

print("\n=== Price vs De-smoothed Price Diagnostics ===")
print(f"Tracking error (monthly % stdev): {te:.2f}%")
print(f"Cross-correlation peak at lag k={best_k} months "
      f"(k>0 means de-smoothed leads reported).")

if SHOW_PLOTS:
    plt.figure(figsize=(9,5))
    aligned["Reported (Appraisal)"].plot(label="Reported (Appraisal)")
    aligned["De-smoothed (Instantaneous)"].plot(label="De-smoothed (Instantaneous)")
    aligned["Benchmark (scaled)"].plot(label="Benchmark (scaled)", alpha=0.6, linestyle="--")
    plt.title("Reported vs De-smoothed Price Index")
    plt.ylabel("Index level"); plt.legend(); plt.tight_layout(); plt.show()

    plt.figure(figsize=(7,3.5))
    plt.stem(list(lags), xcc, use_line_collection=True)
    plt.axhline(0, linewidth=1)
    plt.title("Cross-correlation: Reported vs De-smoothed Returns")
    plt.xlabel("Lag k (months) — k>0: de-smoothed leads")
    plt.tight_layout(); plt.show()