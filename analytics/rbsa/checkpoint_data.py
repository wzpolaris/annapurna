"""
Checkpoint data preparation module.

Prepares data payloads for checkpoint prompt templates. Each checkpoint type
has a corresponding prepare function that extracts and formats relevant information
from the analysis context.
"""
from __future__ import annotations
from typing import Dict, Any, Callable
import pandas as pd


def prepare_post_diagnostics(context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for post-diagnostics checkpoint.

    This checkpoint is triggered after AR(1) autocorrelation testing to let
    the user review desmoothing recommendations.

    Args:
        context: Must contain:
            - ar_test: dict with AR(1) test results including:
                - ar1_coef: AR(1) coefficient
                - ar1_pvalue: p-value for AR(1) test
                - ljungbox_pvalue: Ljung-Box test p-value (optional)
                - n_obs: Number of observations
                - is_significant: Whether autocorrelation is significant

    Returns:
        Formatted data dict with keys:
            - ar1_coef: Formatted AR(1) coefficient
            - ar1_pvalue: Formatted p-value
            - ljungbox_pvalue: Formatted Ljung-Box p-value or 'N/A'
            - n_obs: Number of observations
            - significance: "YES" or "NO"

    Example:
        >>> context = {"ar_test": {"ar1_coef": 0.234, "ar1_pvalue": 0.012, "n_obs": 120, "is_significant": True}}
        >>> data = prepare_post_diagnostics(context)
        >>> print(data["significance"])
        YES
    """
    ar_test = context['ar_test']
    return {
        "ar1_coef": ar_test['ar1_coef'],
        "ar1_pvalue": ar_test['ar1_pvalue'],
        "ljungbox_pvalue": ar_test.get('ljungbox_pvalue', 'N/A'),
        "n_obs": ar_test['n_obs'],
        "significance": "YES" if ar_test['is_significant'] else "NO"
    }


def prepare_candidate_review(context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for candidate review checkpoint.

    This checkpoint is triggered after consolidation of top candidates from
    all approaches (A-D) to let the user review before substitution analysis.

    Args:
        context: Must contain:
            - candidates: list of candidate dicts, each with:
                - selected: list of asset names
                - weights: pd.Series of asset weights
                - diagnostics: dict with r2, adj_r2, rmse, etc.

    Returns:
        Formatted data dict with keys:
            - candidates_summary: Multi-line formatted string
            - n_candidates: Number of candidates

    Example:
        >>> context = {"candidates": [{"selected": ["IWF", "IWD"], "weights": pd.Series(...), "diagnostics": {...}}]}
        >>> data = prepare_candidate_review(context)
        >>> print(data["n_candidates"])
        1
    """
    candidates = context['candidates']

    # Format candidate summary
    lines = []
    for i, c in enumerate(candidates, 1):
        # Format weights for selected assets
        weights_str = ", ".join([
            f"{asset}({c['weights'][asset]:.1%})"
            for asset in c['selected']
            if asset in c['weights'].index
        ])
        lines.append(f"Candidate {i}: {weights_str}")

        # Format diagnostics
        diag = c['diagnostics']
        adj_r2_str = f"{diag.get('adj_r2', 0):.4f}" if 'adj_r2' in diag else 'N/A'
        lines.append(f"  R²={diag['r2']:.4f}, Adj-R²={adj_r2_str}, RMSE={diag['rmse']:.6f}")

    return {
        "candidates_summary": "\n".join(lines),
        "n_candidates": len(candidates)
    }


def prepare_substitution_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare summary of ALL substitution recommendations.

    This checkpoint is triggered after substitution analysis to let the user
    review all recommended consolidations/expansions before applying them.

    Args:
        context: Must contain:
            - sub_results: dict from analyze_substitutions() with structure:
                - candidate_1, candidate_2, etc.: dicts with substitution_tests
            - candidates: original candidates list (for reference)

    Returns:
        Formatted data dict with keys:
            - recommendations_summary: Multi-line formatted string or "(None)"
            - n_candidates_affected: Number of candidates with recommendations
            - n_substitutions: Total number of recommended substitutions

    Example:
        >>> context = {"sub_results": {...}, "candidates": [...]}
        >>> data = prepare_substitution_recommendations(context)
        >>> print(data["n_substitutions"])
        3
    """
    sub_results = context['sub_results']

    # Extract all recommended substitutions across all candidates
    recommendations = []
    candidates_affected = set()

    for candidate_key, result in sub_results.items():
        has_substitutions = False

        for test in result.get("substitution_tests", []):
            r = test.get("result", {})

            # Bottom-up consolidation
            if r.get("applicable") and r.get("recommend_substitution"):
                recommendations.append(
                    f"  • {' + '.join(r['components'])} → {r['substitute']} "
                    f"(Adj-R²: {r['adj_r2_original']:.4f} → {r['adj_r2_substituted']:.4f})"
                )
                has_substitutions = True

            # Top-down expansion
            elif r.get("applicable") and r.get("recommend_expansion"):
                recommendations.append(
                    f"  • {r['substitute']} → {' + '.join(r['components'])} "
                    f"(Adj-R²: {r['adj_r2_original']:.4f} → {r['adj_r2_expanded']:.4f})"
                )
                has_substitutions = True

        if has_substitutions:
            candidates_affected.add(candidate_key)

    return {
        "recommendations_summary": "\n".join(recommendations) if recommendations else "  (None)",
        "n_candidates_affected": len(candidates_affected),
        "n_substitutions": len(recommendations)
    }


def prepare_final_selection(context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for final selection checkpoint.

    This checkpoint is triggered after final ranking to let the user review
    top candidates and select the final model for deployment.

    Args:
        context: Must contain:
            - candidates: list of top N candidates (usually 3), each with:
                - selected: list of asset names
                - weights: pd.Series of asset weights
                - diagnostics: dict with r2, adj_r2, rmse, etc.
                - substitutions_applied: optional list of applied substitutions

    Returns:
        Formatted data dict with keys:
            - candidates_summary: Multi-line formatted string
            - n_options: Number of candidates

    Example:
        >>> context = {"candidates": [{"selected": ["IWB", "EFA"], "weights": pd.Series(...), "diagnostics": {...}}]}
        >>> data = prepare_final_selection(context)
        >>> print(data["n_options"])
        1
    """
    candidates = context['candidates']

    # Format top candidates
    lines = []
    for i, c in enumerate(candidates, 1):
        # Format weights for selected assets
        weights_str = ", ".join([
            f"{asset}({c['weights'][asset]:.1%})"
            for asset in c['selected']
            if asset in c['weights'].index
        ])
        lines.append(f"Option {i}: {weights_str}")

        # Format diagnostics
        diag = c['diagnostics']
        adj_r2_str = f"{diag.get('adj_r2', 0):.4f}" if 'adj_r2' in diag else 'N/A'
        lines.append(f"  R²={diag['r2']:.4f}, Adj-R²={adj_r2_str}")

        # Show substitutions if applied
        if c.get('substitutions_applied'):
            lines.append(f"  Substitutions: {len(c['substitutions_applied'])} applied")

    return {
        "candidates_summary": "\n".join(lines),
        "n_options": len(candidates)
    }


# Registry mapping checkpoint names to prepare functions
PREPARE_FUNCTIONS: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {
    "checkpoint-post-diagnostics": prepare_post_diagnostics,
    "checkpoint-candidate-review": prepare_candidate_review,
    "checkpoint-substitution-recommendations": prepare_substitution_recommendations,
    "checkpoint-final-selection": prepare_final_selection,
}


def prepare_checkpoint_data(checkpoint_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for a checkpoint using registered prepare function.

    This is the main entry point for checkpoint data preparation. It dispatches
    to the appropriate prepare function based on checkpoint name.

    Args:
        checkpoint_name: Name of checkpoint (e.g., "checkpoint-post-diagnostics")
        context: Raw context data from analysis (structure varies by checkpoint)

    Returns:
        Formatted data dict for prompt template interpolation

    Raises:
        KeyError: If checkpoint name not registered in PREPARE_FUNCTIONS
        KeyError: If context is missing required fields (raised by prepare function)

    Example:
        >>> context = {"ar_test": {"ar1_coef": 0.234, ...}}
        >>> data = prepare_checkpoint_data("checkpoint-post-diagnostics", context)
        >>> print(data.keys())
        dict_keys(['ar1_coef', 'ar1_pvalue', 'ljungbox_pvalue', 'n_obs', 'significance'])
    """
    if checkpoint_name not in PREPARE_FUNCTIONS:
        available = list(PREPARE_FUNCTIONS.keys())
        raise KeyError(
            f"No prepare function registered for checkpoint: {checkpoint_name}. "
            f"Available checkpoints: {available}"
        )

    prepare_fn = PREPARE_FUNCTIONS[checkpoint_name]

    try:
        return prepare_fn(context)
    except KeyError as e:
        raise KeyError(
            f"Missing required context data for checkpoint {checkpoint_name}: {e}. "
            f"Check that the context dict contains all required fields."
        )
