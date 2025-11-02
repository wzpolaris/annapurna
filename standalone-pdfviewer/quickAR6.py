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
ANCHOR_MONTH     = "2025-08"      # contiguous overlap ends here (inclusive)
MAX_LAG_MARKET   = 6              # lags for market-anchored de-smoothing
SHOW_PLOTS       = False

# ---- Assumptions for structural models ----
LEVERAGE   = 2.0                  # your leverage multiple (e.g., 2.0 or 3.0)
ANN_MU     = 0.06                 # assumed market expected return (annual, 6%)
ANN_SIGMA  = 0.20                 # assumed market volatility (annual, 20%)
TARGET_MULT     = 1.5             # target total vol >= TARGET_MULT × realized market vol
ENFORCE_REALIZED_BETA = False     # if True, force realized beta ≈ LEVERAGE (hybrid structural only)

# ---- Benchmark fetch ----
BENCH_TICKERS    = ["ACWI", "URTH"]   # try in order
BENCH_START      = "2020-08-01"
BENCH_END        = "2025-09-01"

# ========== CLASS I MONTHLY RETURNS (%) (from your PDF) ==========
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

# ===================== Helpers =====================
def price_from_returns_pp(ret_pp: pd.Series, base=100.0) -> pd.Series:
    """Build a price index from monthly % returns (percent points)."""
    r = (ret_pp/100.0).dropna()
    return (1+r).cumprod()*base

def monthly_tr_proxy_robust(ticker: str, start: str, end: str) -> pd.Series:
    """
    Download daily prices with yfinance using auto_adjust=True and return
    MONTHLY % returns (percent points) as a PeriodIndex(M) Series.
    """
    df = yf.download(ticker, start=start, end=end, auto_adjust=True,
                     progress=False, actions=False, group_by="column")
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if isinstance(df.columns, pd.MultiIndex):
        try:
            px = df.xs("Close", axis=1, level=-1)
            if isinstance(px, pd.DataFrame):
                px = px[ticker] if ticker in px.columns else px.iloc[:,0]
        except Exception:
            px = df.select_dtypes("number").iloc[:,0]
    else:
        px = df["Close"] if "Close" in df.columns else df.select_dtypes("number").iloc[:,0]
    mret = px.resample("M").last().pct_change()*100.0
    return mret.to_period("M")

def adf_pvalue(x):
    x = pd.Series(x).dropna()
    try:
        return adfuller(x)[1]
    except Exception:
        return np.nan

def ac1(x):
    x = pd.Series(x).dropna()
    return x.autocorr(1) if len(x) >= 2 else np.nan

def ann_vol(x): return x.std()*np.sqrt(12)

def ols_alpha_beta(y, x):
    """Regress y on [1, x]. Return (alpha, beta, p(beta), R^2)."""
    df = pd.concat([y, x], axis=1).dropna()
    df.columns = ["y","x"]
    m = sm.OLS(df["y"], sm.add_constant(df["x"])).fit()
    return (m.params.get("const", np.nan),
            m.params.get("x", np.nan),
            m.pvalues.get("x", np.nan),
            m.rsquared)

# ===================== Build reported price index =====================
ci_price = price_from_returns_pp(ci_ret, base=100.0)
ci_price.name = "ci_price"

# ===================== Fetch benchmark (ACWI -> URTH) =====================
mx = pd.Series(dtype=float); BENCH_USED = None
for tk in BENCH_TICKERS:
    mx = monthly_tr_proxy_robust(tk, BENCH_START, BENCH_END)
    if not mx.empty:
        BENCH_USED = tk
        break
if mx.empty:
    raise RuntimeError("Benchmark download failed for ACWI/URTH.")

# ===================== Align contiguous overlap ending ANCHOR_MONTH =====================
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

# ===================== Diagnostics =====================
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

# AR(1) on returns (sanity)
Z = pd.DataFrame({"r": ci_ret, "lag1": ci_ret.shift(1)}).dropna()
ar1 = sm.OLS(Z["r"], sm.add_constant(Z["lag1"])).fit()
print("\n=== AR(1) on returns ===")
print(f"alpha={ar1.params['const']:.3f} (p={ar1.pvalues['const']:.3f}) "
      f"rho={ar1.params['lag1']:.3f} (p={ar1.pvalues['lag1']:.3f})  R2={ar1.rsquared:.3f}")

# ===================== Market-anchored de-smoothing =====================
# r_ci,t = α + Σ_k β_k r_mx,t-k + ε_t  -> move lag exposure to t
df2 = pd.DataFrame({"ci": ci_ret, "mx0": mx})
for k in range(1, MAX_LAG_MARKET+1):
    df2[f"mx{k}"] = mx.shift(k)
Z2 = df2.dropna()
X2 = sm.add_constant(Z2[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]])
ols_mkt = sm.OLS(Z2["ci"], X2).fit()
beta_sum = float(ols_mkt.params[[f"mx{k}" for k in range(0, MAX_LAG_MARKET+1)]].sum())
alpha_m  = float(ols_mkt.params["const"])
resid    = Z2["ci"] - ols_mkt.fittedvalues

# Light whitening of residuals (optional)
rho_e = resid.autocorr(1)
if np.isfinite(rho_e) and abs(rho_e) > 0.1 and abs(1-rho_e) > 1e-6:
    resid_star = (resid - rho_e*resid.shift(1)) / (1 - rho_e)
else:
    resid_star = resid

# CI*: contemporaneous market timing
ci_unsm_mkt = (alpha_m + beta_sum * Z2["mx0"]) + resid_star
ci_unsm_mkt = ci_unsm_mkt.dropna()

# Mean-preserving scaling to target multiple (keeps average return unchanged)
common2 = ci_unsm_mkt.index.intersection(mx.index)
vol_mx   = mx.loc[common2].std()
vol_star = ci_unsm_mkt.loc[common2].std()
mu_star  = ci_unsm_mkt.mean()
scale    = (TARGET_MULT * vol_mx) / vol_star if vol_star > 0 else 1.0
ci_unsm_mkt_scaled = mu_star + (ci_unsm_mkt - mu_star) * scale

# ===================== Structural (Hybrid Leverage) model =====================
# Systematic = LEVERAGE × market (centered so drift comes from assumption unless enforcing realized beta)
# Residuals scaled so total σ >= max( LEVERAGE×σ_assumed , TARGET_MULT×σ_benchmark_realized )
mu_m_assumed_pp = ((1+ANN_MU)**(1/12) - 1) * 100.0       # monthly drift, pp
sigma_m_assumed_pp = (ANN_SIGMA/np.sqrt(12)) * 100.0     # monthly sigma, pp

aligned = pd.concat([mx, resid_star], axis=1).dropna()
aligned.columns = ["mx","eps"]

if ENFORCE_REALIZED_BETA:
    # Force realized beta ≈ LEVERAGE (slope on realized mx equals LEVERAGE)
    lev_market = LEVERAGE * aligned["mx"] + (LEVERAGE * mu_m_assumed_pp - LEVERAGE * aligned["mx"].mean())
else:
    # Center realized mx so drift is fully from assumption; beta often near LEVERAGE
    mx_centered = aligned["mx"] - aligned["mx"].mean()
    lev_market = LEVERAGE * mx_centered + LEVERAGE * mu_m_assumed_pp

lev_sigma  = lev_market.std()
eps_sigma  = aligned["eps"].std()

sigma_leverage_req = LEVERAGE * sigma_m_assumed_pp
sigma_multiple_req = TARGET_MULT * vol_mx
sigma_target_hybrid = max(sigma_leverage_req, sigma_multiple_req)

gap = max(sigma_target_hybrid**2 - lev_sigma**2, 0.0)
k_eps_hybrid = (np.sqrt(gap) / eps_sigma) if eps_sigma > 0 else 0.0
ci_struct_hybrid = (lev_market + k_eps_hybrid * aligned["eps"]).rename(
    f"CI_struct HYBRID (L={LEVERAGE:.1f}{', beta≈L' if ENFORCE_REALIZED_BETA else ''})"
)

# ===================== Structural (CAPM-based) model =====================
# 1) CAPM on de-lagged CI*: β̂_CAPM from CI* ~ α + β MX
capm_df = pd.concat([ci_unsm_mkt, mx], axis=1).dropna()
capm_df.columns = ["ci_star", "mx"]
capm_fit = sm.OLS(capm_df["ci_star"], sm.add_constant(capm_df["mx"])).fit()
beta_hat = float(capm_fit.params["mx"])          # contemporaneous beta estimate

# 2) Systematic beta after leverage: β_sys = LEVERAGE × β̂_CAPM
beta_sys = LEVERAGE * beta_hat

# 3) Build systematic component with assumed drift
mx_centered_capm = capm_df["mx"] - capm_df["mx"].mean()
sys_capm = beta_sys * mx_centered_capm + beta_sys * mu_m_assumed_pp

# 4) Residuals: reuse (lightly whitened) residuals; align indices
eps_capm = resid_star.reindex(capm_df.index).dropna()
sys_capm = sys_capm.reindex(eps_capm.index)

# 5) Hybrid vol targeting for CAPM-structural:
#    sigma_sys = |beta_sys| * stdev(MX). Target >= max( |beta_sys|*σ_assumed_mx , TARGET_MULT*σ_mx_realized )
sigma_sys_capm = abs(beta_sys) * capm_df["mx"].loc[sys_capm.index].std()
sigma_assumed_mx_pp = sigma_m_assumed_pp           # alias
sigma_capm_req = max(abs(beta_sys) * sigma_assumed_mx_pp, TARGET_MULT * capm_df["mx"].std())

gap_capm = max(sigma_capm_req**2 - sigma_sys_capm**2, 0.0)
k_eps_capm = (np.sqrt(gap_capm) / eps_capm.std()) if eps_capm.std() > 0 else 0.0

ci_struct_capm = (sys_capm + k_eps_capm * eps_capm).rename(
    f"CI_struct CAPM (L={LEVERAGE:.1f}, beta_hat={beta_hat:.3f})"
)

# ===================== Summary table =====================
series_map = {
    "CI raw": ci_ret,
    "CI* (mkt-anchored)": ci_unsm_mkt,
    f"CI*s ({TARGET_MULT:.1f}x vol, mean-kept)": ci_unsm_mkt_scaled,
    ci_struct_hybrid.name: ci_struct_hybrid,
    ci_struct_capm.name: ci_struct_capm,
}

print("\n=== Market-anchored de-smoothing (mean-preserving scaling) ===")
print(f"Benchmark used: {BENCH_USED}")
print(f"Sum of betas on mx lags: {beta_sum:.3f}")
print(f"Vols (monthly %, annualized):")
print(f"  MX                             : {mx.std():.2f}%  ({ann_vol(mx):.2f}%)")
print(f"  CI raw                         : {ci_ret.std():.2f}%  ({ann_vol(ci_ret):.2f}%)")
print(f"  CI* (unsm, mkt)                : {ci_unsm_mkt.std():.2f}%  ({ann_vol(ci_unsm_mkt):.2f}%)")
print(f"  CI*s (scaled {TARGET_MULT:.1f}× MX, mean-kept) : {ci_unsm_mkt_scaled.std():.2f}%  ({ann_vol(ci_unsm_mkt_scaled):.2f}%)")
print("\n=== CAPM on CI* ===")
print(f"beta_hat (CI* vs MX) = {beta_hat:.3f}")

def summarize(name, s, x):
    a,b,p,r2 = ols_alpha_beta(s, x)
    return {
        "series": name,
        "mean (pp/mo)": np.nanmean(s),
        "stdev (mo %)": np.nanstd(s),
        "stdev (ann %)": ann_vol(s),
        "beta vs MX": b,
        "p(beta)": p,
        "alpha (pp/mo)": a,
        "AC1": s.autocorr(1)
    }

rows = [summarize(n, s, mx) for n,s in series_map.items()]
tbl = pd.DataFrame(rows)
pd.set_option('display.float_format', lambda v: f"{v:,.3f}")
print("\n=== Summary (aligned window) ===")
print(tbl.to_string(index=False))

# ===================== Visualization =====================
if SHOW_PLOTS:
    base = float(ci_price.dropna().iloc[0])
    ci_px_unsm    = price_from_returns_pp(ci_unsm_mkt.reindex(ci_ret.index), base=base)
    ci_px_unsm_s  = price_from_returns_pp(ci_unsm_mkt_scaled.reindex(ci_ret.index), base=base)
    ci_px_structH = price_from_returns_pp(ci_struct_hybrid.reindex(ci_ret.index), base=base)
    ci_px_structC = price_from_returns_pp(ci_struct_capm.reindex(ci_ret.index), base=base)
    mx_px         = price_from_returns_pp(mx.reindex(ci_ret.index), base=base)

    aligned_px = pd.concat([
        ci_price.rename("Reported (Appraisal)"),
        ci_px_unsm.rename("CI* (mkt-anchored)"),
        ci_px_unsm_s.rename(f"CI*s ({TARGET_MULT:.1f}x vol, mean-kept)"),
        ci_px_structH.rename(ci_struct_hybrid.name),
        ci_px_structC.rename(ci_struct_capm.name),
        mx_px.rename("Benchmark (scaled)")
    ], axis=1).dropna()

    plt.figure(figsize=(11,6))
    aligned_px.plot(ax=plt.gca())
    plt.title("Reported vs De-smoothed / Structural Price Indexes")
    plt.ylabel("Index level")
    plt.tight_layout(); plt.show()

    # Cross-correlation example: Reported vs CAPM-structural returns
    rep_ret = aligned_px["Reported (Appraisal)"].pct_change()*100
    capm_ret = aligned_px[ci_struct_capm.name].pct_change()*100
    lags = range(-6, 7)
    xcc = []
    for k in lags:
        corr = pd.concat([rep_ret, capm_ret.shift(k)], axis=1).dropna().corr().iloc[0,1]
        xcc.append(corr)
    best_k = lags[int(np.nanargmax(xcc))] if len(xcc) else 0
    print(f"\nCross-correlation peak (Reported vs {ci_struct_capm.name}) at k={best_k} months (k>0: structural leads)")

    plt.figure(figsize=(7,3.5))
    plt.stem(list(lags), xcc, use_line_collection=True)
    plt.axhline(0, linewidth=1)
    plt.title(f"Cross-correlation: Reported vs {ci_struct_capm.name} Returns")
    plt.xlabel("Lag k (months)")
    plt.tight_layout(); plt.show()