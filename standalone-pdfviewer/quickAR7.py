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

# ---- CAPM-structural assumptions ----
LEVERAGE   = 2.0                  # leverage multiplier for systematic market exposure
ANN_MU     = 0.06                 # assumed market expected return (annual, 6%)
ANN_SIGMA  = 0.20                 # assumed market volatility (annual, 20%)
TARGET_MULT     = 1.5             # final total vol >= TARGET_MULT × realized market vol

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

# ===================== AR(1) on returns (sanity) =====================
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
ci_star = (alpha_m + beta_sum * Z2["mx0"]) + resid_star
ci_star = ci_star.dropna()

# Mean-preserving scaling to target multiple (keeps average return unchanged)
common2 = ci_star.index.intersection(mx.index)
vol_mx   = mx.loc[common2].std()
vol_star = ci_star.loc[common2].std()
mu_star  = ci_star.mean()
scale    = (TARGET_MULT * vol_mx) / vol_star if vol_star > 0 else 1.0
ci_star_scaled = mu_star + (ci_star - mu_star) * scale

print("\n=== Market-anchored de-smoothing (mean-preserving scaling) ===")
print(f"Benchmark used: {BENCH_USED}")
print(f"Sum of betas on mx lags: {beta_sum:.3f}")
print(f"Vols (monthly %, annualized):")
print(f"  MX                             : {mx.std():.2f}%  ({ann_vol(mx):.2f}%)")
print(f"  CI raw                         : {ci_ret.std():.2f}%  ({ann_vol(ci_ret):.2f}%)")
print(f"  CI* (unsm, mkt)                : {ci_star.std():.2f}%  ({ann_vol(ci_star):.2f}%)")
print(f"  CI*s (scaled {TARGET_MULT:.1f}× MX, mean-kept) : {ci_star_scaled.std():.2f}%  ({ann_vol(ci_star_scaled):.2f}%)")

# ===================== CAPM beta on CI* =====================
capm_df = pd.concat([ci_star, mx], axis=1).dropna()
capm_df.columns = ["ci_star", "mx"]
capm_fit = sm.OLS(capm_df["ci_star"], sm.add_constant(capm_df["mx"])).fit()
beta_hat = float(capm_fit.params["mx"])
print("\n=== CAPM on CI* ===")
print(f"beta_hat (CI* vs MX) = {beta_hat:.3f}")

# ===================== CAPM-Structural with PE Excess Mean (alpha) =====================
# Assumed market drift/vol (monthly, percent points)
mu_M_monthly_pp = ((1+ANN_MU)**(1/12) - 1) * 100.0
sigma_M_monthly_pp = (ANN_SIGMA/np.sqrt(12)) * 100.0

# Systematic beta after leverage
beta_sys = LEVERAGE * beta_hat

# PE excess mean (alpha): match observed mean of CI* by construction
mean_obs = mu_star             # observed mean of CI*
mean_sys = beta_sys * mu_M_monthly_pp
alpha_i  = mean_obs - mean_sys # idiosyncratic expected return (PE excess)

# Systematic component (centered around sample mx mean so constants control drift)
mx_centered = capm_df["mx"] - capm_df["mx"].mean()
sys_capm_alpha = beta_sys * mx_centered + mean_sys + alpha_i

# Residuals for idiosyncratic shock term (aligned)
eps_capm = resid_star.reindex(capm_df.index).dropna()
sys_capm_alpha = sys_capm_alpha.reindex(eps_capm.index)

# Vol targeting (hybrid): target >= max(|beta_sys| * sigma_assumed_mx, TARGET_MULT * realized sigma(mx))
sigma_sys = abs(beta_sys) * capm_df["mx"].loc[sys_capm_alpha.index].std()
sigma_target = max(abs(beta_sys) * sigma_M_monthly_pp, TARGET_MULT * capm_df["mx"].std())

gap = max(sigma_target**2 - sigma_sys**2, 0.0)
k_eps = (np.sqrt(gap) / eps_capm.std()) if eps_capm.std() > 0 else 0.0

ci_struct_capm_alpha = (sys_capm_alpha + k_eps * eps_capm).rename(
    f"CI_struct CAPM+ (L={LEVERAGE:.1f}, beta_hat={beta_hat:.3f})"
)

# ===================== Summary table =====================
series_map = {
    "CI raw": ci_ret,
    "CI* (mkt-anchored)": ci_star,
    f"CI*s ({TARGET_MULT:.1f}x vol, mean-kept)": ci_star_scaled,
    ci_struct_capm_alpha.name: ci_struct_capm_alpha,
}

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

# Extra: show decomposition numbers clearly
print("\n=== CAPM-Structural with alpha: decomposition ===")
print(f"Observed mean CI* (mu_obs)    : {mean_obs:.3f} pp/mo")
print(f"Beta_sys * E[r_M] (mean_sys)  : {mean_sys:.3f} pp/mo  (beta_sys={beta_sys:.3f}, mu_M={mu_M_monthly_pp:.3f})")
print(f"Alpha_i (excess)              : {alpha_i:.3f} pp/mo  (mu_obs - mean_sys)")
print(f"Realized sigma(mx)            : {capm_df['mx'].std():.3f}%/mo")
print(f"Assumed sigma_M (monthly)     : {sigma_M_monthly_pp:.3f}%/mo")
print(f"Target sigma (final)          : {sigma_target:.3f}%/mo")
print(f"Residual scale k_eps          : {k_eps:.3f}")

# ===================== Visualization =====================
if SHOW_PLOTS:
    base = float(ci_price.dropna().iloc[0])
    ci_px_star     = price_from_returns_pp(ci_star.reindex(ci_ret.index), base=base)
    ci_px_star_s   = price_from_returns_pp(ci_star_scaled.reindex(ci_ret.index), base=base)
    ci_px_structCa = price_from_returns_pp(ci_struct_capm_alpha.reindex(ci_ret.index), base=base)
    mx_px          = price_from_returns_pp(mx.reindex(ci_ret.index), base=base)

    aligned_px = pd.concat([
        ci_price.rename("Reported (Appraisal)"),
        ci_px_star.rename("CI* (mkt-anchored)"),
        ci_px_star_s.rename(f"CI*s ({TARGET_MULT:.1f}x vol, mean-kept)"),
        ci_px_structCa.rename(ci_struct_capm_alpha.name),
        mx_px.rename("Benchmark (scaled)")
    ], axis=1).dropna()

    plt.figure(figsize=(11,6))
    aligned_px.plot(ax=plt.gca())
    plt.title("Reported vs De-smoothed / CAPM-Structural(+alpha) Price Indexes")
    plt.ylabel("Index level")
    plt.tight_layout(); plt.show()

    # Cross-correlation: Reported vs CAPM-structural(+alpha) returns
    rep_ret = aligned_px["Reported (Appraisal)"].pct_change()*100
    capm_ret = aligned_px[ci_struct_capm_alpha.name].pct_change()*100
    lags = range(-6, 7)
    xcc = []
    for k in lags:
        corr = pd.concat([rep_ret, capm_ret.shift(k)], axis=1).dropna().corr().iloc[0,1]
        xcc.append(corr)
    best_k = lags[int(np.nanargmax(xcc))] if len(xcc) else 0
    print(f"\nCross-correlation peak (Reported vs {ci_struct_capm_alpha.name}) at k={best_k} months (k>0: structural leads)")

    plt.figure(figsize=(7,3.5))
    plt.stem(list(lags), xcc, use_line_collection=True)
    plt.axhline(0, linewidth=1)
    plt.title(f"Cross-correlation: Reported vs {ci_struct_capm_alpha.name} Returns")
    plt.xlabel("Lag k (months)")
    plt.tight_layout(); plt.show()