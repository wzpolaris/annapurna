from __future__ import annotations
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

def format_weights(w: pd.Series) -> pd.DataFrame:
    return w.sort_values(ascending=False).to_frame("weight")

def candidate_key(cols: List[str]) -> str:
    return "|".join(sorted(cols))

def format_final_results(candidates: List[Dict[str, Any]], show_substitution_label: bool = False) -> str:
    """
    Format final ranked candidates with original compact style.

    Args:
        candidates: List of candidates with 'approach' key (already sorted)
        show_substitution_label: If True, add "(after substitution)" for candidates with substitutions

    Returns:
        Formatted string matching original output style
    """
    output = []

    for i, cand in enumerate(candidates, 1):
        diag = cand.get("diagnostics", {})
        weights = cand.get("weights", pd.Series())
        approach = cand.get("approach", "?")

        # Build label
        label = f"Candidate {i} (Method {approach}"
        if show_substitution_label and len(cand.get("substitutions_applied", [])) > 0:
            label += ", after substitution"
        label += "):"

        output.append(label)

        # Statistics line
        stats_parts = [
            f"n_assets={len(cand['selected'])}",
            f"R²={diag.get('r2', 0):.6f}",
            f"Adj-R²={diag.get('adj_r2', 0):.6f}",
            f"RMSE={diag.get('rmse', 0):.6f}",
            f"MAE={diag.get('mae', 0):.6f}",
        ]

        # Add information criteria if available
        if 'aic' in diag and diag['aic'] is not None:
            stats_parts.extend([
                f"AIC={diag['aic']:.2f}",
                f"AICc={diag['aicc']:.2f}",
                f"BIC={diag['bic']:.2f}",
            ])

        # Add composite score if available
        if 'composite_score' in diag:
            stats_parts.append(f"Composite={diag['composite_score']:.6f}")

        output.append(f"  Statistics: {', '.join(stats_parts)}")

        # Assets line with weights
        if len(weights) > 0:
            sorted_weights = weights.sort_values(ascending=False)
            asset_strs = [f"{asset}({wt:.3f})" for asset, wt in sorted_weights.items()]
            output.append(f"  Assets:     {', '.join(asset_strs)}")
        else:
            output.append(f"  Assets:     (none)")

        output.append("")  # Blank line between candidates

    return "\n".join(output)
