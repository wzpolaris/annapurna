# pip install yfinance statsmodels pandas

import pandas as pd
import numpy as np
import yfinance as yf
import statsmodels.api as sm

# ----- Class I monthly returns (% points) -----
class_i = {
  "2020-09": 0.11, "2020-10": 3.72, "2020-11": 1.52, "2020-12": 2.20,
  "2021-01": 0.00, "2021-02": 0.27, "2021-03": 2.25, "2021-04": 1.28, "2021-05": 1.71, "2021-06": 4.92, "2021-07": 0.17, "2021-08": 2.73, "2021-09": 0.14, "2021-10": 5.18, "2021-11": 0.09, "2021-12": 2.19,
  "2022-01": -1.56, "2022-02": 0.44, "2022-03": 1.67, "2022-04": -1.30, "2022-05": 2.34, "2022-06": -0.68, "2022-07": 4.80, "2022-08": 1.66, "2022-09": -0.74, "2022-10": 4.00, "2022-11": 3.56, "2022-12": 1.20,
  "2023-01": 2.53, "2023-02": 0.12, "2023-03": 1.25, "2023-04": -1.49, "2023-05": 0.20, "2023-06": 2.95, "2023-07": 0.60, "2023-08": -0.79, "2023-09": 1.13, "2023-10": 0.06, "2023-11": 2.25, "2023-12": 3.04,
  "2024-01": 0.66, "2024-02": 0.96, "2024-03": 0.57, "2024-04": -0.90, "2024-05": 0.94, "2024-06": 2.24, "2024-07": 0.33, "2024-08": 1.44, "2024-09": 1.82, "2024-10": -0.53, "2024-11": 2.37, "2024-12": -0.34,
  "2025-01": 1.64, "2025-02": 0.82, "2025-03": 1.29, "2025-04": 1.35, "2025-05": 2.63, "2025-06": 2.59, "2025-07": 0.37, "2025-08": -0.67
}
s_ci = pd.Series(class_i, dtype=float)
s_ci.index = pd.PeriodIndex(s_ci.index, freq="M")

# ----- Robust Yahoo fetch -> monthly TR proxy as a Series (PeriodIndex M) -----
def monthly_tr_proxy(ticker: str) -> pd.Series:
    df = yf.download(
        ticker, start="2020-08-01", end="2025-09-01",
        auto_adjust=False, progress=False, group_by="ticker"
    )
    if df is None or df.empty:
        return pd.Series(dtype=float)

    # Handle both simple columns and MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        # expect hierarchy: [ticker][field]
        try:
            adj = df[ticker]["Adj Close"]
        except Exception:
            # fall back: try to find the 'Adj Close' level anywhere
            level_names = [str(x) for x in df.columns.get_level_values(-1)]
            if "Adj Close" in level_names:
                adj = df.xs("Adj Close", axis=1, level=-1)
                # If still wide (multiple tickers), pick our ticker
                if isinstance(adj, pd.DataFrame) and ticker in adj.columns:
                    adj = adj[ticker]
            else:
                return pd.Series(dtype=float)
    else:
        # single-level columns
        if "Adj Close" not in df.columns:
            return pd.Series(dtype=float)
        adj = df["Adj Close"]

    # Resample to month-end and compute pct change (percent points)
    mret = adj.resample("M").last().pct_change() * 100.0

    # Coerce to Series (if it accidentally became 1-col DataFrame)
    if isinstance(mret, pd.DataFrame):
        if mret.shape[1] == 1:
            mret = mret.iloc[:, 0]
        else:
            # pick our ticker if present
            if ticker in mret.columns:
                mret = mret[ticker]
            else:
                # last resort: first column
                mret = mret.iloc[:, 0]

    s = mret.to_period("M")
    s.name = ticker
    return s

s_msci = monthly_tr_proxy("ACWI")
if s_msci.empty:
    s_msci = monthly_tr_proxy("URTH")
    if s_msci.empty:
        raise RuntimeError("Failed to download ACWI/URTH monthly returns. Check network/ticker.")

# Sanity: both Series, PeriodIndex(M)
assert isinstance(s_ci, pd.Series)
assert isinstance(s_msci, pd.Series)
if not isinstance(s_msci.index, pd.PeriodIndex):
    s_msci = s_msci.to_period("M")
if s_msci.index.freqstr != "M":
    s_msci.index = pd.PeriodIndex(s_msci.index, freq="M")

# ----- Contiguous overlap ending 2025-08 -----
anchor = pd.Period("2025-08", freq="M")
common = s_ci.index.intersection(s_msci.index)
common = common[common <= anchor]
if len(common) == 0:
    raise ValueError("No common months <= 2025-08.")

contig = pd.period_range(start=common.min(), end=anchor, freq="M")
ci = s_ci.reindex(contig)
mx = s_msci.reindex(contig)

# Trim leading NaNs so window is contiguous
start = max(ci.first_valid_index(), mx.first_valid_index())
ci = ci[ci.index >= start]
mx = mx[mx.index >= start]

# Final contiguous window
window = ci.index.intersection(mx.index)
ci = ci.reindex(window)
mx = mx.reindex(window)

# Robust NA check (bool-ify to avoid ambiguous truth)
if bool(ci.isna().any()) or bool(mx.isna().any()):
    raise ValueError("Non-contiguous data after trimming; found NaNs in ci or mx.")

print(f"Contiguous window: {window[0]} → {window[-1]}  (n={len(window)})")

# ----- Difference series: Class I − MSCI proxy (percent points) -----
diff = (ci - mx)
diff.name = "ClassI_minus_MSCIproxy"
assert isinstance(diff, pd.Series) and len(diff) >= 8

# ----- AR(p), p = 1..4 (joint) -----
def run_ar(y: pd.Series):
    results = {p: _fit_ar_p(y, p) for p in range(1, 5)}
    # ----- Print results -----
    for p, r in results.items():
        parts = [f"AIC={r['AIC']:.3f}" if pd.notna(r['AIC']) else "AIC=nan",
                f"R²={r['R2']:.3f}" if pd.notna(r['R2']) else "R²=nan"]
        for i in range(1, p+1):
            rho, pr = r.get(f"rho{i}"), r.get(f"p_rho{i}")
            parts.append(f"ρ{i}={rho: .3f} (p={pr: .3f})" if pd.notna(rho) and pd.notna(pr)
                        else f"ρ{i}=nan (p=nan)")
        print(f"AR({p})  " + "  ".join(parts))


def _fit_ar_p(y: pd.Series, p: int):
    z = pd.DataFrame({"y": y})
    for i in range(1, p + 1):
        z[f"lag{i}"] = z["y"].shift(i)
    z = z.dropna()
    if z.empty:
        return {"AIC": np.nan, "R2": np.nan,
                **{f"rho{i}": np.nan for i in range(1,p+1)},
                **{f"p_rho{i}": np.nan for i in range(1,p+1)},
                "const": np.nan, "p_const": np.nan}
    X = sm.add_constant(z[[f"lag{i}" for i in range(1, p + 1)]])
    m = sm.OLS(z["y"], X).fit()
    out = {"AIC": m.aic, "R2": m.rsquared,
           "const": m.params.get("const", np.nan),
           "p_const": m.pvalues.get("const", np.nan)}
    for i in range(1, p + 1):
        out[f"rho{i}"] = m.params.get(f"lag{i}", np.nan)
        out[f"p_rho{i}"] = m.pvalues.get(f"lag{i}", np.nan)
    return out

print('diff')
run_ar(diff)

print('')
print('ci')
run_ar(ci)

print('')
print('mx')
run_ar(mx)

import statsmodels.api as sm

# Align and drop missing
aligned = pd.concat([ci, mx], axis=1).dropna()
aligned.columns = ["ci", "mx"]

X = sm.add_constant(aligned["mx"])
y = aligned["ci"]
ols = sm.OLS(y, X).fit()

print(ols.summary())