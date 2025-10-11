from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from ..rbsa_utils import rolling_origin_splits, hac_se, model_diagnostics
from ..optimization import nnls_simplex

def stepwise_nnls(X: pd.DataFrame, y: pd.Series, max_k: int, sum_to_one: bool, eps_rmse: float, mode: str = "in_sample") -> List[str]:
    candidates = list(X.columns)
    chosen = []
    best_metric = np.inf if mode == "prediction" else -np.inf  # RMSE (lower better) vs R² (higher better)

    # Start with best single variable
    if len(candidates) == 0:
        return chosen

    while len(chosen) < max_k and len(candidates) > 0:
        trial_scores = []
        for c in candidates:
            cols = chosen + [c]
            w = nnls_simplex(X[cols].values, y.values, sum_to_one=sum_to_one)
            resid = y.values - X[cols].values.dot(w)

            if mode == "in_sample":
                # Use R² (higher is better)
                ss_res = np.sum(resid**2)
                ss_tot = np.sum((y.values - y.values.mean())**2)
                metric = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            else:
                # Use RMSE (lower is better)
                metric = np.sqrt(np.mean(resid**2))

            trial_scores.append((metric, c))

        trial_scores.sort(reverse=(mode == "in_sample"))  # descending for R², ascending for RMSE

        # First iteration: always accept best variable
        if len(chosen) == 0:
            best_metric = trial_scores[0][0]
            chosen.append(trial_scores[0][1])
            candidates.remove(trial_scores[0][1])
            continue

        # Subsequent iterations: check for improvement
        if mode == "in_sample":
            # For R²: if improvement is significant
            if trial_scores[0][0] - eps_rmse > best_metric:
                best_metric = trial_scores[0][0]
                chosen.append(trial_scores[0][1])
                candidates.remove(trial_scores[0][1])
            else:
                break
        else:
            # For RMSE: if improvement is significant
            if trial_scores[0][0] + eps_rmse < best_metric:
                best_metric = trial_scores[0][0]
                chosen.append(trial_scores[0][1])
                candidates.remove(trial_scores[0][1])
            else:
                break

    return chosen

def fit_one(X: pd.DataFrame, y: pd.Series, cols: List[str], sum_to_one: bool) -> Dict[str, Any]:
    if len(cols) == 0:
        # Return empty result if no columns selected
        return {
            "weights": pd.Series(dtype=float),
            "residuals": pd.Series(y.values, index=y.index),
            "yhat": pd.Series(np.zeros(len(y)), index=y.index),
            "hac_se": np.array([])
        }

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

def approach_A_pipeline(X: pd.DataFrame, y: pd.Series, cfg: Dict[str, Any]) -> Dict[str, Any]:
    max_k = cfg["approach_A"]["max_subset_size"]
    sum_to_one = not cfg["approach_A"]["allow_cash_less_than_one"]
    eps = cfg["approach_A"]["stepwise_epsilon_rmse"]
    mode = cfg.get("analysis", {}).get("mode", "in_sample")
    # simple forward stepwise then refit
    cols = stepwise_nnls(X, y, max_k=max_k, sum_to_one=sum_to_one, eps_rmse=eps, mode=mode)
    result = fit_one(X, y, cols, sum_to_one=sum_to_one)
    result["selected"] = cols
    result["diagnostics"] = model_diagnostics(y, result["yhat"], result["residuals"], k=len(cols))
    return result
