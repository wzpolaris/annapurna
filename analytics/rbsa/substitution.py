from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
from .optimization import nnls_simplex
from .rbsa_utils import model_diagnostics


def test_weight_swap(
    X: pd.DataFrame,
    y: pd.Series,
    components: List[str],
    original_weights: pd.Series,
    sum_to_one: bool = True
) -> Dict[str, Any]:
    """
    Test if swapping weights between components makes a meaningful difference.

    Args:
        X: Asset returns
        y: Fund returns
        components: List of component assets to swap (e.g., ["IWF", "IWD"])
        original_weights: Original weight allocation
        sum_to_one: Whether weights sum to 1

    Returns:
        Dict with swap results and diagnostics
    """
    # Create swapped weights
    swapped_weights = original_weights.copy()

    # Swap the weights of the components
    if len(components) == 2 and all(c in swapped_weights.index for c in components):
        swapped_weights[components[0]], swapped_weights[components[1]] = \
            swapped_weights[components[1]], swapped_weights[components[0]]
    else:
        return {"error": "Cannot swap - components not found or invalid"}

    # Calculate predictions with swapped weights
    assets = swapped_weights.index.tolist()
    yhat_swapped = X[assets].values.dot(swapped_weights.values)
    resid_swapped = y.values - yhat_swapped

    # Calculate original predictions
    yhat_original = X[assets].values.dot(original_weights.values)
    resid_original = y.values - yhat_original

    # Diagnostics
    diag_swapped = model_diagnostics(y, pd.Series(yhat_swapped, index=y.index), pd.Series(resid_swapped, index=y.index), k=len(assets))
    diag_original = model_diagnostics(y, pd.Series(yhat_original, index=y.index), pd.Series(resid_original, index=y.index), k=len(assets))

    # Calculate differences
    r2_diff = diag_swapped["r2"] - diag_original["r2"]
    rmse_diff = diag_swapped["rmse"] - diag_original["rmse"]

    return {
        "swapped_weights": swapped_weights,
        "diagnostics_swapped": diag_swapped,
        "diagnostics_original": diag_original,
        "r2_difference": r2_diff,
        "rmse_difference": rmse_diff,
        "materially_different": abs(r2_diff) > 0.001  # Threshold for material difference
    }


def test_substitution(
    X: pd.DataFrame,
    y: pd.Series,
    substitute: str,
    components: List[str],
    original_weights: pd.Series,
    sum_to_one: bool = True
) -> Dict[str, Any]:
    """
    Test if components can be replaced with a substitute asset.

    Args:
        X: Asset returns (must include substitute)
        y: Fund returns
        substitute: Substitute asset (e.g., "IWB")
        components: Component assets to replace (e.g., ["IWF", "IWD"])
        original_weights: Original weight allocation
        sum_to_one: Whether weights sum to 1

    Returns:
        Dict with substitution results and recommendation
    """
    # Check if substitute is available
    if substitute not in X.columns:
        return {"error": f"Substitute asset {substitute} not available in data"}

    # Check if components exist in original weights
    components_present = [c for c in components if c in original_weights.index]
    if len(components_present) == 0:
        return {"error": "No components found in original weights", "applicable": False}

    if len(components_present) < len(components):
        return {"error": f"Only {components_present} found, not all of {components}", "applicable": False}

    # Calculate substitute weight as sum of component weights
    substitute_weight = sum(original_weights[c] for c in components_present)

    # Create new weight vector with substitution
    other_assets = [a for a in original_weights.index if a not in components_present]
    new_assets = other_assets + [substitute]
    new_weights_values = [original_weights[a] for a in other_assets] + [substitute_weight]
    new_weights = pd.Series(new_weights_values, index=new_assets)

    # Normalize if needed
    if sum_to_one:
        new_weights = new_weights / new_weights.sum()

    # Calculate predictions with substitution
    yhat_substituted = X[new_assets].values.dot(new_weights.values)
    resid_substituted = y.values - yhat_substituted

    # Calculate original predictions
    original_assets = original_weights.index.tolist()
    yhat_original = X[original_assets].values.dot(original_weights.values)
    resid_original = y.values - yhat_original

    # Diagnostics
    diag_substituted = model_diagnostics(y, pd.Series(yhat_substituted, index=y.index), pd.Series(resid_substituted, index=y.index), k=len(new_assets))
    diag_original = model_diagnostics(y, pd.Series(yhat_original, index=y.index), pd.Series(resid_original, index=y.index), k=len(original_assets))

    # Calculate differences
    r2_diff = diag_substituted["r2"] - diag_original["r2"]
    rmse_diff = diag_substituted["rmse"] - diag_original["rmse"]

    # Calculate adjusted R² for both
    n_obs = len(y)
    adj_r2_original = 1 - (1 - diag_original["r2"]) * (n_obs - 1) / (n_obs - len(original_assets) - 1)
    adj_r2_substituted = 1 - (1 - diag_substituted["r2"]) * (n_obs - 1) / (n_obs - len(new_assets) - 1)
    adj_r2_diff = adj_r2_substituted - adj_r2_original

    # Recommendation logic
    recommend_substitution = (
        (r2_diff > -0.001) or  # R² doesn't decline by more than 0.001
        (adj_r2_diff > 0)      # OR Adjusted R² actually improves (parsimony wins)
    )

    return {
        "applicable": True,
        "substitute": substitute,
        "components": components_present,
        "substitute_weight": substitute_weight,
        "new_weights": new_weights,
        "diagnostics_original": diag_original,
        "diagnostics_substituted": diag_substituted,
        "adj_r2_original": adj_r2_original,
        "adj_r2_substituted": adj_r2_substituted,
        "r2_difference": r2_diff,
        "rmse_difference": rmse_diff,
        "adj_r2_difference": adj_r2_diff,
        "recommend_substitution": recommend_substitution,
        "num_assets_saved": len(components_present) - 1
    }


def test_expansion(
    X: pd.DataFrame,
    y: pd.Series,
    substitute: str,
    components: List[str],
    original_weights: pd.Series,
    sum_to_one: bool = True
) -> Dict[str, Any]:
    """
    Test if a composite asset should be expanded into its components.

    Top-down expansion: If IWM is in the model, test if splitting into IWO+IWN improves fit.

    Args:
        X: Asset returns (must include components)
        y: Fund returns
        substitute: Composite asset currently in model (e.g., "IWM")
        components: Component assets to expand into (e.g., ["IWO", "IWN"])
        original_weights: Original weight allocation
        sum_to_one: Whether weights sum to 1

    Returns:
        Dict with expansion results and recommendation
    """
    # Check if substitute exists in original weights
    if substitute not in original_weights.index:
        return {"error": f"Substitute asset {substitute} not in original weights", "applicable": False}

    # Check if components are available
    missing_components = [c for c in components if c not in X.columns]
    if missing_components:
        return {"error": f"Components not available: {missing_components}", "applicable": False}

    substitute_weight = original_weights[substitute]

    # Create new weight vector with expansion
    # Other assets keep their weights, substitute is replaced with components
    other_assets = [a for a in original_weights.index if a != substitute]
    expanded_assets = other_assets + components

    # Optimize with NNLS
    expanded_weights_values = nnls_simplex(X[expanded_assets].values, y.values, sum_to_one=sum_to_one)
    expanded_weights = pd.Series(expanded_weights_values, index=expanded_assets)

    # Calculate predictions with expansion
    yhat_expanded = X[expanded_assets].values.dot(expanded_weights_values)
    resid_expanded = y.values - yhat_expanded

    # Calculate original predictions
    original_assets = original_weights.index.tolist()
    yhat_original = X[original_assets].values.dot(original_weights.values)
    resid_original = y.values - yhat_original

    # Diagnostics
    diag_expanded = model_diagnostics(y, pd.Series(yhat_expanded, index=y.index), pd.Series(resid_expanded, index=y.index), k=len(expanded_assets))
    diag_original = model_diagnostics(y, pd.Series(yhat_original, index=y.index), pd.Series(resid_original, index=y.index), k=len(original_assets))

    # Calculate differences
    r2_diff = diag_expanded["r2"] - diag_original["r2"]
    rmse_diff = diag_expanded["rmse"] - diag_original["rmse"]

    # Calculate adjusted R² for both
    n_obs = len(y)
    adj_r2_original = 1 - (1 - diag_original["r2"]) * (n_obs - 1) / (n_obs - len(original_assets) - 1)
    adj_r2_expanded = 1 - (1 - diag_expanded["r2"]) * (n_obs - 1) / (n_obs - len(expanded_assets) - 1)
    adj_r2_diff = adj_r2_expanded - adj_r2_original

    # Recommendation logic for expansion
    recommend_expansion = (
        (r2_diff > 0.001) or  # R² improves by more than threshold
        (adj_r2_diff > 0)     # OR Adjusted R² improves (more granular information wins)
    )

    return {
        "applicable": True,
        "substitute": substitute,
        "components": components,
        "original_substitute_weight": substitute_weight,
        "expanded_weights": expanded_weights,
        "diagnostics_original": diag_original,
        "diagnostics_expanded": diag_expanded,
        "adj_r2_original": adj_r2_original,
        "adj_r2_expanded": adj_r2_expanded,
        "r2_difference": r2_diff,
        "rmse_difference": rmse_diff,
        "adj_r2_difference": adj_r2_diff,
        "recommend_expansion": recommend_expansion,
        "num_assets_added": len(components) - 1
    }


def analyze_substitutions(
    candidates: List[Dict[str, Any]],
    X: pd.DataFrame,
    y: pd.Series,
    substitution_rules: List[Dict[str, Any]],
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Analyze all candidates for potential substitutions.

    Args:
        candidates: List of candidate models
        X: Asset returns
        y: Fund returns
        substitution_rules: List of substitution rules from config
        verbose: Print detailed analysis

    Returns:
        Dict with substitution analysis for each candidate
    """
    results = {}

    for idx, candidate in enumerate(candidates):
        if verbose:
            print(f"\n{'='*80}")
            print(f"Candidate {idx + 1}: {', '.join(candidate['selected'])}")
            print(f"{'='*80}")

        candidate_results = {
            "original_weights": candidate["weights"],
            "substitution_tests": [],
            "swap_tests": []
        }

        # Test each substitution rule
        for rule in substitution_rules:
            substitute = rule["substitute"]
            components = rule["components"]
            direction = rule.get("direction", "bottom-up")

            # Bottom-up: consolidate components into substitute
            if direction == "bottom-up":
                # Check if all components are present
                if all(c in candidate["selected"] for c in components):
                    if verbose:
                        print(f"\n✓ Found {' + '.join(components)} → Testing bottom-up consolidation to {substitute}")

                # Test weight swap
                swap_result = test_weight_swap(X, y, components, candidate["weights"])
                candidate_results["swap_tests"].append({
                    "rule": rule["name"],
                    "components": components,
                    "result": swap_result
                })

                if verbose:
                    if "error" not in swap_result:
                        print(f"\n  Weight Swap Test ({components[0]} ↔ {components[1]}):")
                        print(f"    Original weights: {components[0]}={candidate['weights'][components[0]]:.3f}, {components[1]}={candidate['weights'][components[1]]:.3f}")
                        print(f"    Swapped weights:  {components[0]}={swap_result['swapped_weights'][components[0]]:.3f}, {components[1]}={swap_result['swapped_weights'][components[1]]:.3f}")
                        print(f"    R² difference: {swap_result['r2_difference']:+.6f}")
                        print(f"    RMSE difference: {swap_result['rmse_difference']:+.6f}")
                        print(f"    Materially different: {swap_result['materially_different']}")

                # Test substitution
                sub_result = test_substitution(X, y, substitute, components, candidate["weights"])
                candidate_results["substitution_tests"].append({
                    "rule": rule["name"],
                    "result": sub_result
                })

                if verbose and sub_result.get("applicable"):
                    print(f"\n  Substitution Test ({' + '.join(components)} → {substitute}):")
                    print(f"    Combined weight: {sub_result['substitute_weight']:.3f}")
                    print(f"    Original:    R²={sub_result['diagnostics_original']['r2']:.6f}, Adj-R²={sub_result['adj_r2_original']:.6f}, RMSE={sub_result['diagnostics_original']['rmse']:.6f}")
                    print(f"    Substituted: R²={sub_result['diagnostics_substituted']['r2']:.6f}, Adj-R²={sub_result['adj_r2_substituted']:.6f}, RMSE={sub_result['diagnostics_substituted']['rmse']:.6f}")
                    print(f"    Differences: ΔR²={sub_result['r2_difference']:+.6f}, ΔAdj-R²={sub_result['adj_r2_difference']:+.6f}, ΔRMSE={sub_result['rmse_difference']:+.6f}")
                    print(f"    Assets saved: {sub_result['num_assets_saved']}")
                    print(f"    {'✓ RECOMMEND SUBSTITUTION' if sub_result['recommend_substitution'] else '✗ Keep original components'}")

                elif verbose:
                    present = [c for c in components if c in candidate["selected"]]
                    if present:
                        print(f"\n  Partial match: Found {present} but not all of {components}")

            # Top-down: expand substitute into components
            elif direction == "top-down":
                # Check if substitute is present
                if substitute in candidate["selected"]:
                    if verbose:
                        print(f"\n✓ Found {substitute} → Testing top-down expansion to {' + '.join(components)}")

                    # Test expansion
                    exp_result = test_expansion(X, y, substitute, components, candidate["weights"])
                    candidate_results["substitution_tests"].append({
                        "rule": rule["name"],
                        "result": exp_result
                    })

                    if verbose and exp_result.get("applicable"):
                        print(f"\n  Expansion Test ({substitute} → {' + '.join(components)}):")
                        print(f"    Original weight: {exp_result['original_substitute_weight']:.3f}")
                        print(f"    Expanded weights: {', '.join([f'{c}={exp_result["expanded_weights"][c]:.3f}' for c in components])}")
                        print(f"    Original:  R²={exp_result['diagnostics_original']['r2']:.6f}, Adj-R²={exp_result['adj_r2_original']:.6f}, RMSE={exp_result['diagnostics_original']['rmse']:.6f}")
                        print(f"    Expanded:  R²={exp_result['diagnostics_expanded']['r2']:.6f}, Adj-R²={exp_result['adj_r2_expanded']:.6f}, RMSE={exp_result['diagnostics_expanded']['rmse']:.6f}")
                        print(f"    Differences: ΔR²={exp_result['r2_difference']:+.6f}, ΔAdj-R²={exp_result['adj_r2_difference']:+.6f}, ΔRMSE={exp_result['rmse_difference']:+.6f}")
                        print(f"    Assets added: {exp_result['num_assets_added']}")
                        print(f"    {'✓ RECOMMEND EXPANSION' if exp_result['recommend_expansion'] else '✗ Keep original composite'}")

                elif verbose:
                    print(f"\n  {substitute} not found in model (needed for top-down expansion)")

        results[f"candidate_{idx + 1}"] = candidate_results

    # Count total recommendations
    total_recommendations = 0
    for candidate_result in results.values():
        for test in candidate_result.get("substitution_tests", []):
            result = test.get("result", {})
            if result.get("applicable") and result.get("recommend_substitution"):
                total_recommendations += 1

    # Print summary
    if verbose:
        print(f"\n{'='*80}")
        if total_recommendations > 0:
            print(f"✓ {total_recommendations} substitution{'s' if total_recommendations != 1 else ''} recommended")
        else:
            print("○ No substitutions recommended")
        print(f"{'='*80}")

    return results


def apply_recommended_substitutions(
    candidates: List[Dict[str, Any]],
    substitution_results: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    cfg: Dict[str, Any],
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Apply recommended substitutions and create new candidate list.

    Args:
        candidates: Original top candidates
        substitution_results: Results from analyze_substitutions
        X: Asset returns (full universe)
        y: Fund returns
        cfg: Configuration
        verbose: Print details

    Returns:
        Updated list of candidates with substitutions applied
    """
    from .rbsa_utils import model_diagnostics

    updated_candidates = []
    mode = cfg.get("analysis", {}).get("mode", "in_sample")

    if verbose:
        print(f"\n{'='*80}")
        print("APPLYING RECOMMENDED SUBSTITUTIONS")
        print(f"{'='*80}")

    for idx, candidate in enumerate(candidates):
        candidate_key = f"candidate_{idx + 1}"
        candidate_result = substitution_results.get(candidate_key, {})

        # Start with original
        updated_candidate = candidate.copy()
        updated_candidate["original_selected"] = candidate["selected"].copy()
        updated_candidate["substitutions_applied"] = []

        # Group substitution tests by components to find best substitute
        component_groups = {}
        for test in candidate_result.get("substitution_tests", []):
            result = test.get("result", {})
            if not result.get("applicable"):
                continue

            # Bottom-up consolidation
            if "recommend_substitution" in result and result["recommend_substitution"]:
                components = tuple(sorted(result["components"]))  # Use tuple as dict key

                # Track all viable substitutes for these components
                if components not in component_groups:
                    component_groups[components] = []

                component_groups[components].append({
                    "substitute": result["substitute"],
                    "adj_r2": result["adj_r2_substituted"],
                    "result": result
                })

        # Apply only the BEST substitute for each component group
        for components, substitutes in component_groups.items():
            # Sort by Adj-R² (higher is better)
            substitutes.sort(key=lambda x: x["adj_r2"], reverse=True)
            best = substitutes[0]
            result = best["result"]
            substitute = best["substitute"]

            if verbose:
                if len(substitutes) > 1:
                    print(f"\n✓ Multiple substitutes tested for {' + '.join(components)}:")
                    for sub in substitutes:
                        print(f"  - {sub['substitute']}: Adj-R²={sub['adj_r2']:.6f}")
                    print(f"  → Choosing BEST: {substitute} (Adj-R²={best['adj_r2']:.6f})")
                else:
                    print(f"\n✓ Applying: {' + '.join(components)} → {substitute}")

                print(f"  Original R²={result['diagnostics_original']['r2']:.6f}, New R²={result['diagnostics_substituted']['r2']:.6f}")

            # Replace components with best substitute
            new_selected = [a for a in updated_candidate["selected"] if a not in components]
            new_selected.append(substitute)
            new_weights = result["new_weights"]

            updated_candidate["selected"] = new_selected
            updated_candidate["weights"] = new_weights
            updated_candidate["substitutions_applied"].append({
                "type": "consolidation",
                "from": list(components),
                "to": substitute,
                "adj_r2": best["adj_r2"]
            })

        # Handle top-down expansions (unchanged logic)
        for test in candidate_result.get("substitution_tests", []):
            result = test.get("result", {})
            if not result.get("applicable"):
                continue

            # Top-down expansion
            elif "recommend_expansion" in result and result["recommend_expansion"]:
                substitute = result["substitute"]
                components = result["components"]

                if verbose:
                    print(f"\n✓ Applying: {substitute} → {' + '.join(components)}")
                    print(f"  Original R²={result['diagnostics_original']['r2']:.6f}, New R²={result['diagnostics_expanded']['r2']:.6f}")

                # Replace substitute with components
                new_selected = [a for a in updated_candidate["selected"] if a != substitute]
                new_selected.extend(components)
                new_weights = result["expanded_weights"]

                updated_candidate["selected"] = new_selected
                updated_candidate["weights"] = new_weights
                updated_candidate["substitutions_applied"].append({
                    "type": "expansion",
                    "from": substitute,
                    "to": components
                })

        # Recalculate diagnostics with final weights
        if len(updated_candidate["selected"]) > 0:
            assets = updated_candidate["selected"]
            weights = updated_candidate["weights"]
            yhat = X[assets].values.dot(weights.values)
            resid = y.values - yhat

            updated_candidate["yhat"] = pd.Series(yhat, index=y.index)
            updated_candidate["residuals"] = pd.Series(resid, index=y.index)
            updated_candidate["diagnostics"] = model_diagnostics(y, updated_candidate["yhat"], updated_candidate["residuals"], k=len(assets))

            if verbose:
                if len(updated_candidate["substitutions_applied"]) > 0:
                    print(f"\n  Updated diagnostics:")
                    print(f"    R²={updated_candidate['diagnostics']['r2']:.6f}")
                    print(f"    RMSE={updated_candidate['diagnostics']['rmse']:.6f}")
                    print(f"    Assets: {', '.join(updated_candidate['selected'])}")

        updated_candidates.append(updated_candidate)

    # Re-rank based on mode
    if verbose:
        print(f"\n{'='*80}")
        print("RE-RANKING AFTER SUBSTITUTIONS")
        print(f"{'='*80}")

    for c in updated_candidates:
        if mode == "in_sample":
            # Higher R² is better, negate for sorting
            c["score"] = -c.get("diagnostics", {}).get("r2", -np.inf)
        else:
            # Lower RMSE is better
            c["score"] = c.get("diagnostics", {}).get("rmse", np.inf)

    # Sort by score
    updated_candidates.sort(key=lambda x: x["score"])

    if verbose:
        print(f"\nNew Rankings ({mode} mode):")
        for i, c in enumerate(updated_candidates):
            r2 = c["diagnostics"].get("r2", np.nan)
            rmse = c["diagnostics"].get("rmse", np.nan)
            n_subs = len(c["substitutions_applied"])
            subs_str = f" ({n_subs} substitution{'s' if n_subs != 1 else ''})" if n_subs > 0 else ""
            print(f"  {i+1}. R²={r2:.6f}, RMSE={rmse:.6f} - {', '.join(c['selected'])}{subs_str}")

    # If any substitutions were applied, print formatted final results
    any_substitutions = any(len(c.get("substitutions_applied", [])) > 0 for c in updated_candidates)

    if any_substitutions and verbose:
        from .reporting import format_final_results
        print(f"\n{'='*80}")
        print("FINAL CANDIDATES AFTER SUBSTITUTIONS")
        print(f"{'='*80}\n")
        print(format_final_results(updated_candidates, show_substitution_label=True))

    return updated_candidates
