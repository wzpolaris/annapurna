"""
Final comprehensive summarization using LLM.
"""
from __future__ import annotations
import pandas as pd
from typing import Dict, Any, List
from .rbsa_utils import Summarizer


def format_candidates_for_summary(candidates: List[Dict[str, Any]]) -> str:
    """
    Format candidate results into a text summary for LLM analysis.

    Args:
        candidates: List of top candidate models

    Returns:
        Formatted text describing all candidates
    """
    lines = []
    lines.append("RBSA ANALYSIS RESULTS")
    lines.append("=" * 80)
    lines.append("")

    for i, c in enumerate(candidates[:5], 1):  # Top 5
        lines.append(f"Candidate {i}:")

        # Assets and weights
        weights = c.get("weights", pd.Series())
        if len(weights) > 0:
            asset_strs = [f"{asset} ({weights[asset]:.1%})" for asset in c["selected"] if asset in weights.index]
            lines.append(f"  Assets: {', '.join(asset_strs)}")
        else:
            lines.append(f"  Assets: {', '.join(c['selected'])}")

        # Diagnostics
        diag = c.get("diagnostics", {})
        lines.append(f"  R²: {diag.get('r2', 0):.4f}")
        lines.append(f"  Adjusted R²: {diag.get('adj_r2', 0):.4f}")
        lines.append(f"  RMSE: {diag.get('rmse', 0):.6f}")

        # Information criteria if available
        if 'aic' in diag and diag['aic'] is not None:
            lines.append(f"  AIC: {diag['aic']:.2f}, AICc: {diag['aicc']:.2f}, BIC: {diag['bic']:.2f}")

        # Substitutions if applied
        if "substitutions_applied" in c and len(c["substitutions_applied"]) > 0:
            subs = c["substitutions_applied"]
            sub_strs = [f"{s['from']} → {s['to']}" if isinstance(s['from'], list) else f"{s['from']} → {', '.join(s['to'])}" for s in subs]
            lines.append(f"  Substitutions: {'; '.join(sub_strs)}")

        lines.append("")

    return "\n".join(lines)


def generate_final_summary(
    candidates: List[Dict[str, Any]],
    summarizer: Summarizer,
    analysis_mode: str = "in_sample",
    desmooth_applied: bool = False
) -> str:
    """
    Generate comprehensive AI summary of RBSA results.

    Args:
        candidates: Top candidate models (post-substitution)
        summarizer: Summarizer instance
        analysis_mode: "in_sample" or "prediction"
        desmooth_applied: Whether de-smoothing was applied

    Returns:
        AI-generated summary text
    """
    # Format candidate data
    candidates_text = format_candidates_for_summary(candidates)

    # Build prompt
    prompt_parts = [
        candidates_text,
        "",
        "CONTEXT:",
        f"- Analysis mode: {analysis_mode}",
        f"- De-smoothing applied: {'Yes' if desmooth_applied else 'No'}",
        "",
        "INSTRUCTIONS:",
        "Analyze the top RBSA candidates and provide:",
        "1. Key insights about the portfolio's factor exposures (equity vs fixed income, growth vs value, etc.)",
        "2. Commentary on model quality (R², fit statistics, parsimony)",
        "3. Notable differences between top candidates",
        "4. Any concerns or recommendations (concentration risk, substitution choices, etc.)",
        "",
        "Be specific, concise, and actionable. Focus on economic interpretation."
    ]

    prompt = "\n".join(prompt_parts)

    # Generate summary
    summary = summarizer.summarize(prompt)

    return summary


def create_summary_report(
    candidates: List[Dict[str, Any]],
    summarizer: Summarizer,
    cfg: Dict[str, Any],
    desmooth_diagnostics: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Create comprehensive summary report with multiple sections.

    Args:
        candidates: Top candidate models
        summarizer: Summarizer instance
        cfg: Configuration dict
        desmooth_diagnostics: Optional de-smoothing diagnostics

    Returns:
        Dict with summary sections
    """
    analysis_mode = cfg.get("analysis", {}).get("mode", "in_sample")
    desmooth_applied = desmooth_diagnostics is not None and desmooth_diagnostics.get("desmoothed", False)

    # Main summary
    main_summary = generate_final_summary(candidates, summarizer, analysis_mode, desmooth_applied)

    # Additional context
    context_lines = []
    context_lines.append("ANALYSIS CONFIGURATION:")
    context_lines.append(f"  Mode: {analysis_mode}")
    context_lines.append(f"  Number of candidates: {len(candidates)}")

    if desmooth_applied:
        ar_test = desmooth_diagnostics.get("ar1_test", {})
        context_lines.append(f"  De-smoothing: Applied (original AR(1)={ar_test.get('ar1_coef', 0):.4f})")
    else:
        context_lines.append(f"  De-smoothing: Not needed")

    context = "\n".join(context_lines)

    return {
        "main": main_summary,
        "context": context,
        "full": f"{context}\n\n{'='*80}\nAI ANALYSIS\n{'='*80}\n\n{main_summary}"
    }
