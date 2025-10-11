from __future__ import annotations
import os, sys, yaml
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .checkpoints import CheckpointRunner
from .data_loader import load_fund_returns, load_portfolio, download_prices, to_monthly_returns, align_and_merge, compute_excess, compute_portfolio_returns
from .prelim import winsorize, pca_summary, correlation_clustering, pick_medoids, simple_regime_marks
from .models.approach_a import approach_A_pipeline
from .models.approach_b import approach_B_pipeline
from .models.approach_c import approach_C_pipeline
from .models.approach_d import approach_D_pipeline
from .reporting import format_weights
from .rbsa_utils import Summarizer
from .desmoothing import desmooth_if_needed

def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_raw_data(cfg: Dict[str, Any], project_root: str) -> Dict[str, Any]:
    """
    Load raw fund and benchmark data before preprocessing.

    Returns dict with 'y', 'X_all', 'rf_series', 'tickers', 'substitution_tickers'
    """
    # Check if portfolio_csv is configured
    portfolio_csv = cfg["data"].get("portfolio_csv")

    if portfolio_csv:
        # Load portfolio and compute weighted returns
        portfolio_path = os.path.join(project_root, portfolio_csv)
        print(f"Loading portfolio from {portfolio_csv}")
        portfolio = load_portfolio(portfolio_path)
        print(f"Portfolio: {len(portfolio)} holdings")
        print(portfolio)

        # Compute portfolio returns
        fund_returns = compute_portfolio_returns(
            portfolio,
            cfg["data"]["price_download_start"],
            cfg["data"]["price_download_end"],
            cfg["data"]["frequency"]
        )
        # Convert to DataFrame with expected format
        fund = pd.DataFrame({"date": fund_returns.index, "fund_return": fund_returns.values})
    else:
        # Use traditional fund returns CSV
        fund_csv = os.path.join(project_root, cfg["data"]["fund_returns_csv"])
        fund = load_fund_returns(fund_csv)

    # Download data for both selection and substitution-only tickers
    tickers = cfg["universe"]["tickers"]
    substitution_tickers = cfg["universe"].get("substitution_only", [])
    all_tickers = tickers + substitution_tickers

    print(f"Downloading {len(tickers)} selection tickers + {len(substitution_tickers)} substitution-only tickers")

    prices = download_prices(all_tickers, cfg["data"]["price_download_start"], cfg["data"]["price_download_end"])
    rets = to_monthly_returns(prices, cfg["data"]["frequency"]).dropna(how="all")

    # Separate selection vs substitution assets
    rf = None
    if cfg["data"]["risk_free_ticker"] in rets.columns:
        rf = rets[cfg["data"]["risk_free_ticker"]]

    y, X_all, rf_series = align_and_merge(fund, rets, rf)

    return {
        "y": y,
        "X_all": X_all,
        "rf_series": rf_series,
        "tickers": tickers,
        "substitution_tickers": substitution_tickers
    }


def prepare_data(
    cfg: Dict[str, Any],
    project_root: str,
    raw_data: Dict[str, Any] = None,
    checkpoint_runner: Optional['CheckpointRunner'] = None
) -> Dict[str, Any]:
    """
    Prepare data for RBSA analysis with preprocessing.

    Args:
        cfg: Configuration dict
        project_root: Project root directory
        raw_data: Optional pre-loaded raw data from load_raw_data()
        checkpoint_runner: Optional CheckpointRunner for human-in-the-loop interaction.
            If provided, user may be prompted at key decision points during data prep.

    Returns:
        Dict with 'y', 'X', 'X_full', and optional 'desmooth_diagnostics'

    Note:
        Backward compatible: Works identically when checkpoint_runner=None.
    """
    # Load raw data if not provided
    if raw_data is None:
        raw_data = load_raw_data(cfg, project_root)

    y = raw_data["y"]
    X_all = raw_data["X_all"]
    rf_series = raw_data["rf_series"]
    tickers = raw_data["tickers"]
    substitution_tickers = raw_data["substitution_tickers"]

    # Test for autocorrelation and de-smooth if needed
    desmooth_config = cfg.get("preprocessing", {}).get("desmooth", {})
    if desmooth_config.get("enabled", False):
        significance_level = desmooth_config.get("significance_level", 0.05)
        verbose = desmooth_config.get("verbose", True)
        y, desmooth_diagnostics = desmooth_if_needed(
            y,
            significance_level=significance_level,
            verbose=verbose,
            checkpoint_runner=checkpoint_runner
        )
    else:
        desmooth_diagnostics = None

    # X contains only selection tickers (exclude substitution-only)
    X = X_all[[col for col in X_all.columns if col in tickers]]

    print(f"Selection universe: {len(X.columns)} assets")
    print(f"Full universe (including substitutions): {len(X_all.columns)} assets")
    # Excess returns for both selection and full universe
    X_ex = compute_excess(X, rf_series)
    X_all_ex = compute_excess(X_all, rf_series)
    y_ex = y - (rf_series if rf_series is not None else 0.0)

    # Winsorize
    X_ex = winsorize(X_ex, cfg["prelim"]["winsorize_pct"])
    X_all_ex = winsorize(X_all_ex, cfg["prelim"]["winsorize_pct"])
    y_ex = y_ex.clip(y_ex.quantile(cfg["prelim"]["winsorize_pct"]), y_ex.quantile(1-cfg["prelim"]["winsorize_pct"]))

    # Drop any rows with NaN in either y or X
    y_clean = y_ex.dropna()
    X_clean = X_ex.loc[y_clean.index]
    X_all_clean = X_all_ex.loc[y_clean.index]

    # Drop any columns in X with NaN
    X_clean = X_clean.dropna(axis=1)
    X_all_clean = X_all_clean.dropna(axis=1)

    # Drop any remaining rows with NaN
    valid_idx = X_clean.dropna(axis=0).index
    X_clean = X_clean.loc[valid_idx]
    X_all_clean = X_all_clean.loc[valid_idx]
    y_clean = y_clean.loc[valid_idx]

    print(f"After cleaning: {len(y_clean)} observations, {len(X_clean.columns)} selection assets, {len(X_all_clean.columns)} total assets")

    result = {"y": y_clean, "X": X_clean, "X_full": X_all_clean}
    if desmooth_diagnostics is not None:
        result["desmooth_diagnostics"] = desmooth_diagnostics

    return result

def run_all_methods(cfg: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
    X, y = data["X"], data["y"]
    results = {}
    results["A"] = approach_A_pipeline(X, y, cfg)
    results["B"] = approach_B_pipeline(X, y, cfg)
    results["C"] = approach_C_pipeline(X, y, cfg)
    results["D"] = approach_D_pipeline(X, y, cfg)
    return results

def summarize_result(res: Dict[str, Any], summarizer: Summarizer) -> str:
    txt = []
    txt.append(f"Selected assets: {', '.join(res['selected'])}")
    d = res.get("diagnostics", {})
    txt.append(f"RMSE={d.get('rmse',''):.6f}, MAE={d.get('mae',''):.6f}")
    w = res["weights"].sort_values(ascending=False)
    txt.append(f"Weights: {', '.join([f'{i}:{w[i]:.2f}' for i in w.index])}")
    return summarizer.summarize("\n".join(txt))

def finalize_results(all_candidates: List[Dict[str, Any]], cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Rank all candidates by performance metric.

    Returns:
        List of candidates sorted by score (best first)
    """
    mode = cfg.get("analysis", {}).get("mode", "in_sample")

    for c in all_candidates:
        if mode == "in_sample":
            c["score"] = c.get("diagnostics", {}).get("r2", -np.inf)  # Higher is better
        else:
            c["score"] = -c.get("diagnostics", {}).get("rmse", np.inf)  # Lower RMSE is better, negate for sorting

    # Sort descending (higher score = better)
    return sorted(all_candidates, key=lambda d: d.get("score", -np.inf), reverse=True)

def main(project_root: str) -> Dict[str, Any]:
    cfg = load_config(os.path.join(project_root, "config.yaml"))
    data = prepare_data(cfg, project_root)
    results = run_all_methods(cfg, data)
    summarizer = Summarizer(
        backend=cfg["summarization"]["backend"],
        model=cfg["summarization"]["model"],
        temperature=cfg["summarization"]["temperature"],
        system_prompt=cfg["summarization"]["system_prompt"],
    )
    for k,v in results.items():
        v["summary"] = summarize_result(v, summarizer)
    # Final consolidation with approach labels
    all_cands = [
        {"approach": "A", **results["A"]},
        {"approach": "B", **results["B"]},
        {"approach": "C", **results["C"]},
        {"approach": "D", **results["D"]},
    ]
    results["final"] = finalize_results(all_cands, cfg)
    return results

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(__file__))
    out = main(root)
    print({k: (list(v["selected"]) if k != "final" else "final") for k,v in out.items() if k in ["A","B","D","final"]})
