from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from ..rbsa_utils import hac_se, model_diagnostics
from ..optimization import nnls_simplex


def dirichlet_spike_slab_mcmc(
    X: pd.DataFrame,
    y: pd.Series,
    n_samples: int = 5000,
    n_burnin: int = 1000,
    pip_threshold: float = 0.5,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Bayesian RBSA with Dirichlet prior on weights and spike-and-slab for inclusion.

    Args:
        X: Asset returns (excess)
        y: Fund returns (excess)
        n_samples: Number of MCMC samples
        n_burnin: Number of burn-in samples
        pip_threshold: Posterior inclusion probability threshold
        verbose: Print progress

    Returns:
        Dictionary with selected assets, posterior inclusion probabilities, weight distributions
    """
    n_obs = len(y)
    n_assets = len(X.columns)
    assets = X.columns.tolist()

    if verbose:
        print(f"\nBayesian RBSA with Dirichlet-Spike Prior")
        print(f"{'='*80}")
        print(f"Running MCMC: {n_samples} samples, {n_burnin} burn-in")

    # Prior hyperparameters
    alpha_dir = np.ones(n_assets)  # Dirichlet prior (uniform)
    prior_inclusion = 0.3  # Prior probability of inclusion per asset
    tau_spike = 0.01  # Variance for spike (near-zero weights)
    tau_slab = 1.0    # Variance for slab (active weights)
    sigma2_prior_shape = 2.0  # Inverse-Gamma shape for error variance
    sigma2_prior_scale = 0.01  # Inverse-Gamma scale for error variance

    # Initialize
    gamma = np.random.binomial(1, prior_inclusion, n_assets)  # Inclusion indicators
    w = np.random.dirichlet(alpha_dir)  # Weights (simplex)
    sigma2 = 0.001  # Error variance

    # Storage for posterior samples
    gamma_samples = np.zeros((n_samples - n_burnin, n_assets))
    w_samples = np.zeros((n_samples - n_burnin, n_assets))
    sigma2_samples = np.zeros(n_samples - n_burnin)
    log_likelihood_samples = np.zeros(n_samples - n_burnin)

    X_vals = X.values
    y_vals = y.values

    # MCMC sampling
    for i in range(n_samples):
        # 1. Update inclusion indicators gamma (Gibbs step for each asset)
        for j in range(n_assets):
            # Likelihood ratio for including vs excluding asset j
            w_temp_in = w.copy()
            w_temp_out = w.copy()
            w_temp_out[j] = 0

            # Renormalize excluding asset j
            if w_temp_out.sum() > 0:
                w_temp_out = w_temp_out / w_temp_out.sum()

            resid_in = y_vals - X_vals.dot(w_temp_in)
            resid_out = y_vals - X_vals.dot(w_temp_out)

            ll_in = -0.5 * np.sum(resid_in**2) / sigma2
            ll_out = -0.5 * np.sum(resid_out**2) / sigma2

            # Use log-sum-exp trick for numerical stability
            log_prior_odds = np.log(prior_inclusion / (1 - prior_inclusion))
            log_posterior_odds = (ll_in - ll_out) + log_prior_odds

            # Convert to probability using stable formula
            if log_posterior_odds > 20:  # Very likely to include
                posterior_prob = 1.0
            elif log_posterior_odds < -20:  # Very unlikely to include
                posterior_prob = 0.0
            else:
                posterior_prob = 1.0 / (1.0 + np.exp(-log_posterior_odds))

            # Clip to valid range [0, 1]
            posterior_prob = np.clip(posterior_prob, 0.0, 1.0)

            gamma[j] = np.random.binomial(1, posterior_prob)

        # 2. Update weights w | gamma (Metropolis-Hastings on simplex)
        active = gamma > 0
        n_active = active.sum()

        if n_active > 0:
            # Propose new weights via Dirichlet perturbation
            proposal_alpha = w[active] * 100 + 0.1  # Concentrate around current
            w_prop_active = np.random.dirichlet(proposal_alpha)
            w_prop = np.zeros(n_assets)
            w_prop[active] = w_prop_active

            # Compute acceptance ratio
            resid_curr = y_vals - X_vals.dot(w)
            resid_prop = y_vals - X_vals.dot(w_prop)

            ll_curr = -0.5 * np.sum(resid_curr**2) / sigma2
            ll_prop = -0.5 * np.sum(resid_prop**2) / sigma2

            # Dirichlet prior ratio (symmetric, cancels in this case)
            accept_ratio = np.exp(ll_prop - ll_curr)

            if np.random.uniform() < accept_ratio:
                w = w_prop
        else:
            # If no assets selected, sample uniform
            w = np.ones(n_assets) / n_assets

        # 3. Update error variance sigma2 (Gibbs step, Inverse-Gamma)
        resid = y_vals - X_vals.dot(w)
        sse = np.sum(resid**2)

        shape_post = sigma2_prior_shape + n_obs / 2
        scale_post = sigma2_prior_scale + sse / 2

        sigma2 = 1.0 / np.random.gamma(shape_post, 1.0 / scale_post)

        # Store samples after burn-in
        if i >= n_burnin:
            idx = i - n_burnin
            gamma_samples[idx, :] = gamma
            w_samples[idx, :] = w
            sigma2_samples[idx] = sigma2
            log_likelihood_samples[idx] = -0.5 * n_obs * np.log(2 * np.pi * sigma2) - 0.5 * sse / sigma2

        if verbose and (i + 1) % 1000 == 0:
            print(f"  Iteration {i+1}/{n_samples}, active assets: {active.sum()}, sigma²={sigma2:.6f}")

    # Calculate posterior inclusion probabilities (PIP)
    pip = gamma_samples.mean(axis=0)

    # Get assets with PIP >= threshold
    selected_idx = pip >= pip_threshold
    selected_assets = [assets[i] for i in range(n_assets) if selected_idx[i]]

    # Posterior mean weights for selected assets
    w_posterior_mean = w_samples.mean(axis=0)
    w_posterior_std = w_samples.std(axis=0)

    # Credible intervals (95%)
    w_posterior_lower = np.percentile(w_samples, 2.5, axis=0)
    w_posterior_upper = np.percentile(w_samples, 97.5, axis=0)

    if verbose:
        print(f"\nPosterior Inclusion Probabilities (PIP):")
        pip_df = pd.DataFrame({
            'asset': assets,
            'PIP': pip,
            'mean_weight': w_posterior_mean,
            'std_weight': w_posterior_std
        }).sort_values('PIP', ascending=False)
        print(pip_df.to_string(index=False))

        print(f"\nSelected assets (PIP >= {pip_threshold}): {', '.join(selected_assets) if selected_assets else '(none)'}")

    # Refit with NNLS using selected assets for final weights
    if len(selected_assets) > 0:
        w_final = nnls_simplex(X[selected_assets].values, y.values, sum_to_one=True)
        yhat = X[selected_assets].values.dot(w_final)
        resid = y.values - yhat

        result = {
            "weights": pd.Series(w_final, index=selected_assets),
            "residuals": pd.Series(resid, index=y.index),
            "yhat": pd.Series(yhat, index=y.index),
            "hac_se": hac_se(X[selected_assets].values, resid)
        }
    else:
        # No assets selected
        result = {
            "weights": pd.Series(dtype=float),
            "residuals": pd.Series(y.values, index=y.index),
            "yhat": pd.Series(np.zeros(len(y)), index=y.index),
            "hac_se": np.array([])
        }

    # Add Bayesian-specific outputs
    result["pip"] = pd.Series(pip, index=assets)
    result["posterior_mean_weights"] = pd.Series(w_posterior_mean, index=assets)
    result["posterior_std_weights"] = pd.Series(w_posterior_std, index=assets)
    result["posterior_weight_lower"] = pd.Series(w_posterior_lower, index=assets)
    result["posterior_weight_upper"] = pd.Series(w_posterior_upper, index=assets)
    result["mcmc_samples"] = {
        "gamma": gamma_samples,
        "weights": w_samples,
        "sigma2": sigma2_samples,
        "log_likelihood": log_likelihood_samples
    }

    return result


def approach_C_pipeline(X: pd.DataFrame, y: pd.Series, cfg: Dict[str, Any], verbose: bool = False) -> Dict[str, Any]:
    """
    Approach C: Bayesian RBSA with Dirichlet-spike prior.

    Provides:
    - Posterior inclusion probabilities (PIP)
    - Credible intervals on weights
    - Model uncertainty quantification
    """
    n_samples = cfg.get("approach_C", {}).get("mcmc_samples", 5000)
    n_burnin = cfg.get("approach_C", {}).get("mcmc_burnin", 1000)
    pip_threshold = cfg.get("approach_C", {}).get("pip_threshold", 0.5)

    result = dirichlet_spike_slab_mcmc(X, y, n_samples, n_burnin, pip_threshold, verbose)

    # Select assets based on PIP
    selected_assets = result["pip"][result["pip"] >= pip_threshold].index.tolist()
    result["selected"] = selected_assets

    # Compute diagnostics
    result["diagnostics"] = model_diagnostics(y, result["yhat"], result["residuals"], k=len(selected_assets))

    if verbose:
        print(f"\n{'='*80}")
        print(f"Final NNLS weights (PIP >= {pip_threshold}):")
        if len(result["weights"]) > 0:
            for asset, wt in result["weights"].sort_values(ascending=False).items():
                pip_val = result["pip"][asset]
                print(f"  {asset}: {wt:.4f} (PIP={pip_val:.3f})")
        else:
            print("  (no assets selected)")

        print(f"\nDiagnostics: R²={result['diagnostics'].get('r2', 0):.4f}, RMSE={result['diagnostics'].get('rmse', 0):.6f}")

    return result
