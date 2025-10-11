from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from ..rbsa_utils import hac_se, model_diagnostics
from ..optimization import nnls_simplex

def elasticnet_select(X: pd.DataFrame, y: pd.Series, alphas: list, n_lambdas: int, one_se: bool, cv_splits: int = 5, verbose: bool = False) -> List[str]:
    from ..optimization import nnls_simplex

    scaler = StandardScaler(with_mean=True, with_std=True)
    Xs = scaler.fit_transform(X.values)
    # l1_ratio in sklearn = alpha (L1 ratio). We'll grid over it.
    nonzero_counts = {}

    if verbose:
        print(f"\nElasticNet Selection (testing {len([a for a in alphas if a != 0])} l1_ratio values):")
        print("=" * 80)

    for a in alphas:
        # Skip l1_ratio=0 (pure Ridge) as ElasticNetCV doesn't support auto alpha grid for it
        if a == 0:
            if verbose:
                print(f"  l1_ratio={a:.2f}: SKIPPED (pure Ridge not supported)")
            continue

        en = ElasticNetCV(l1_ratio=a, alphas=n_lambdas, fit_intercept=True, cv=cv_splits, max_iter=10000, n_jobs=None)
        en.fit(Xs, y.values)
        coef = en.coef_
        nz = [X.columns[i] for i, c in enumerate(coef) if abs(c) > 1e-10]

        if verbose:
            print(f"\n  l1_ratio={a:.2f}: Selected {len(nz)} assets: {', '.join(nz) if nz else '(none)'}")
            # Show top 3 coefficients
            coef_df = pd.DataFrame({'asset': X.columns, 'coef': coef}).sort_values('coef', key=abs, ascending=False)
            print(f"              Top coefficients: {', '.join([f'{row.asset}={row.coef:.3f}' for _, row in coef_df.head(3).iterrows()])}")

            # Refit with NNLS using selected assets (if any)
            if len(nz) > 0:
                w_nnls = nnls_simplex(X[nz].values, y.values, sum_to_one=True)
                yhat_nnls = X[nz].values.dot(w_nnls)
                resid_nnls = y.values - yhat_nnls

                # Calculate metrics
                mse = np.mean(resid_nnls**2)
                mae = np.mean(np.abs(resid_nnls))
                ss_res = np.sum(resid_nnls**2)
                ss_tot = np.sum((y.values - y.values.mean())**2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

                # Adjusted R² = 1 - (1-R²) * (n-1)/(n-p-1)
                n = len(y)
                p = len(nz)
                adj_r2 = 1 - (1 - r2) * (n - 1) / (n - p - 1) if n > p + 1 else r2

                print(f"              RBSA refit: R²={r2:.4f}, Adj-R²={adj_r2:.4f}, MSE={mse:.6f}, MAE={mae:.6f}")

                # Show weights (show all, even tiny ones that round to .000)
                weights_series = pd.Series(w_nnls, index=nz).sort_values(ascending=False)
                weights_str = ', '.join([f'{asset}={wt:.3f}' for asset, wt in weights_series.items()])
                print(f"              Weights: {weights_str}")
            else:
                print(f"              RBSA refit: (no assets selected)")

        for z in nz:
            nonzero_counts[z] = nonzero_counts.get(z, 0) + 1

    # keep variables that appear in majority of alpha settings
    valid_alphas = [a for a in alphas if a != 0]
    threshold = max(1, int(0.5*len(valid_alphas)))

    if verbose:
        print(f"\nSelection frequency (need >={threshold}/{len(valid_alphas)} to be selected):")
        for k, v in sorted(nonzero_counts.items(), key=lambda x: -x[1]):
            print(f"  {k}: {v}/{len(valid_alphas)}")

    keep = [k for k, v in nonzero_counts.items() if v >= threshold]

    if len(keep) == 0:
        # fallback to top coefficients from the last fit
        keep = [X.columns[int(np.argmax(np.abs(coef)))]]
        if verbose:
            print(f"\nNo assets met threshold, using fallback: {keep}")
    else:
        if verbose:
            print(f"\nFinal selected assets: {', '.join(keep)}")

    return keep

def fit_refit_nnls(X: pd.DataFrame, y: pd.Series, cols: List[str], sum_to_one: bool) -> Dict[str, Any]:
    w = nnls_simplex(X[cols].values, y.values, sum_to_one=sum_to_one)
    yhat = X[cols].values.dot(w)
    resid = y.values - yhat
    se = hac_se(X[cols].values, resid)
    return {
        "weights": pd.Series(w, index=cols),
        "residuals": pd.Series(resid, index=y.index),
        "yhat": pd.Series(yhat, index=y.index),
        "hac_se": se
    }

def approach_B_pipeline(X: pd.DataFrame, y: pd.Series, cfg: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    alphas = cfg["approach_B"]["alpha_grid"]
    nlam = cfg["approach_B"]["lambda_grid_points"]
    one_se = cfg["approach_B"]["one_se_rule"]
    sum_to_one = not cfg["approach_A"]["allow_cash_less_than_one"]
    cols = elasticnet_select(X, y, alphas, nlam, one_se, cv_splits=5, verbose=verbose)
    # Optional: trim by selection freq via bootstrap could be added here
    if verbose:
        print(f"\n{'='*80}")
        print(f"Refitting with NNLS (sum_to_one={sum_to_one})...")
    result = fit_refit_nnls(X, y, cols, sum_to_one=sum_to_one)
    result["selected"] = cols
    result["diagnostics"] = model_diagnostics(y, result["yhat"], result["residuals"], k=len(cols))
    if verbose:
        print(f"Final weights:")
        for asset, weight in result["weights"].items():
            print(f"  {asset}: {weight:.4f}")
        print(f"\nDiagnostics: RMSE={result['diagnostics'].get('rmse', 'N/A'):.6f}")
    return result
