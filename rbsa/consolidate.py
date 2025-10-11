from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from .rbsa_utils import calculate_composite_score


def order_assets_by_hierarchy(assets: List[str], weights: pd.Series) -> List[tuple]:
    """
    Order assets by hierarchy: Equity > Fixed Income > Other, US > Non-US, Large > Small, etc.

    Returns:
        List of (asset, weight) tuples in hierarchical order
    """
    # Define asset categories and ordering
    equity_us_large = ["SPY", "IVV", "VOO", "IWB", "VV"]  # S&P 500, Russell 1000
    equity_us_large_growth = ["IWF", "VUG"]  # Russell 1000 Growth
    equity_us_large_value = ["IWD", "VTV"]  # Russell 1000 Value
    equity_us_mid = ["IJH", "MDY", "VO"]  # Mid cap
    equity_us_small = ["IWM", "IJR", "VB"]  # Russell 2000, Small cap
    equity_us_small_growth = ["IWO", "VBK"]  # Russell 2000 Growth
    equity_us_small_value = ["IWN", "VBR"]  # Russell 2000 Value
    equity_us_broad = ["IWV", "VTI", "ITOT"]  # Russell 3000, Total market

    equity_intl_developed = ["EFA", "VEA", "IEFA"]  # EAFE
    equity_intl_emerging = ["EEM", "VWO", "IEMG"]  # Emerging markets

    fixed_income_treas_short = ["SHY", "VGSH"]  # 1-3Y Treasury
    fixed_income_treas_inter = ["IEF", "VGIT"]  # 7-10Y Treasury
    fixed_income_treas_long = ["TLT", "VGLT"]  # 20+ Treasury
    fixed_income_tips = ["TIP", "VTIP", "SCHP"]  # TIPS
    fixed_income_ig_corp = ["LQD", "VCIT"]  # Investment grade corporate
    fixed_income_hy = ["HYG", "JNK"]  # High yield
    fixed_income_muni = ["MUB", "VTEB"]  # Municipal
    fixed_income_broad = ["AGG", "BND"]  # Aggregate bond

    cash = ["BIL", "SHV"]  # Cash equivalents
    commodities = ["DBC", "GSG", "PDBC"]  # Commodities
    gold = ["GLD", "IAU"]  # Gold
    real_estate = ["VNQ", "IYR"]  # REITs

    # Create ordering
    hierarchy = []
    hierarchy.extend(equity_us_broad)
    hierarchy.extend(equity_us_large)
    hierarchy.extend(equity_us_large_growth)
    hierarchy.extend(equity_us_large_value)
    hierarchy.extend(equity_us_mid)
    hierarchy.extend(equity_us_small)
    hierarchy.extend(equity_us_small_growth)
    hierarchy.extend(equity_us_small_value)
    hierarchy.extend(equity_intl_developed)
    hierarchy.extend(equity_intl_emerging)
    hierarchy.extend(fixed_income_broad)
    hierarchy.extend(fixed_income_treas_short)
    hierarchy.extend(fixed_income_treas_inter)
    hierarchy.extend(fixed_income_treas_long)
    hierarchy.extend(fixed_income_tips)
    hierarchy.extend(fixed_income_ig_corp)
    hierarchy.extend(fixed_income_hy)
    hierarchy.extend(fixed_income_muni)
    hierarchy.extend(cash)
    hierarchy.extend(real_estate)
    hierarchy.extend(gold)
    hierarchy.extend(commodities)

    # Create ordered list
    ordered = []
    for asset_group in [hierarchy]:
        for h_asset in hierarchy:
            if h_asset in assets:
                ordered.append((h_asset, weights.get(h_asset, 0.0)))

    # Add any assets not in hierarchy (alphabetically at end)
    remaining = sorted([a for a in assets if a not in hierarchy])
    for asset in remaining:
        ordered.append((asset, weights.get(asset, 0.0)))

    return ordered


def format_final_results(candidates: List[Dict[str, Any]], n_obs: int, show_all_metrics: bool = True) -> None:
    """
    Format final candidate results with comprehensive metrics and composite score.
    Prints two rows per candidate: statistics row and assets row.

    Args:
        candidates: List of candidate models (each has 'selected', 'weights', 'diagnostics')
        n_obs: Number of observations in the dataset
        show_all_metrics: If True, show AIC, AICc, BIC, composite score
    """
    from .rbsa_utils import calculate_composite_score

    print("\n" + "="*100)
    print("FINAL RESULTS")
    print("="*100)

    for i, c in enumerate(candidates):
        # Get diagnostics
        diag = c["diagnostics"]
        r2 = diag.get("r2", np.nan)
        adj_r2 = diag.get("adj_r2", np.nan)
        rmse = diag.get("rmse", np.nan)
        mae = diag.get("mae", np.nan)
        aic = diag.get("aic", np.nan)
        aicc = diag.get("aicc", np.nan)
        bic = diag.get("bic", np.nan)

        # Calculate composite score
        comp_scores = calculate_composite_score(diag, n_obs)
        composite = comp_scores["composite_raw"]

        # Print statistics row
        print(f"\nCandidate {i+1}:")
        print(f"  Statistics: n_assets={len(c['selected'])}, R²={r2:.6f}, Adj-R²={adj_r2:.6f}, RMSE={rmse:.6f}, MAE={mae:.6f}", end="")
        if show_all_metrics:
            print(f", AIC={aic:.2f}, AICc={aicc:.2f}, BIC={bic:.2f}, Composite={composite:.6f}")
        else:
            print()

        # Order assets and format with weights
        weights = c.get("weights", pd.Series())
        ordered_assets = order_assets_by_hierarchy(c["selected"], weights)
        assets_str = ", ".join([f"{asset}({wt:.3f})" for asset, wt in ordered_assets])

        print(f"  Assets:     {assets_str}")

    # Add note about sample size weighting
    if show_all_metrics and len(candidates) > 0:
        print("\n" + "-"*100)
        weights_used = calculate_composite_score(candidates[0]["diagnostics"], n_obs)["weights_used"]
        note = f"Note: Composite score uses n={n_obs} → weights: R²={weights_used['r2']:.0%}, Adj-R²={weights_used['adj_r2']:.0%}, AICc={weights_used['aicc']:.0%}, BIC={weights_used['bic']:.0%}"
        print(note)
        if n_obs < 60:
            print("Small sample detected (n<60): AICc emphasized, BIC de-emphasized")
        else:
            print("Large sample (n≥60): BIC emphasized")
        print("Lower AIC/AICc/BIC is better. Higher composite score is better.")
        print("="*100)


def rank_by_composite(candidates: List[Dict[str, Any]], n_obs: int) -> List[Dict[str, Any]]:
    """
    Re-rank candidates by composite score.

    Args:
        candidates: List of candidate models
        n_obs: Number of observations

    Returns:
        Sorted list of candidates (best first)
    """
    # Calculate composite scores
    for c in candidates:
        comp_scores = calculate_composite_score(c["diagnostics"], n_obs)
        c["composite_score"] = comp_scores["composite_raw"]
        c["composite_details"] = comp_scores

    # Sort by composite score (higher is better)
    ranked = sorted(candidates, key=lambda x: x["composite_score"], reverse=True)

    return ranked


def create_diagnostic_questions(candidates: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Create diagnostic questions DataFrame for each candidate.

    Args:
        candidates: List of candidate models

    Returns:
        DataFrame with diagnostic questions
    """
    questions = []
    for i, c in enumerate(candidates):
        questions.append({
            "rank": i + 1,
            "q1": "If the fund's mandate restricts leverage/cash, does the weight mix comply?",
            "q2": "Would a different commodity spec (e.g., PDBC vs DBC) change stability materially?"
        })

    return pd.DataFrame(questions).set_index("rank")
