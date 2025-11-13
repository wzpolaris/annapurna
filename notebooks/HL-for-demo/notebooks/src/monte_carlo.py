"""Monte Carlo utilities for unified privates model.

Simulate factor paths and map them into private return distributions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .unified_model import factor_returns_to_privates


def simulate_factors_normal(factors_hist: pd.DataFrame,
                            n_paths: int = 10000,
                            n_steps: int | None = None,
                            rng: np.random.Generator | None = None) -> np.ndarray:
    """Simulate factor returns using a multivariate normal approximation.

    Parameters
    ----------
    factors_hist : DataFrame
        Historical factor returns (T x k).
    n_paths : int
        Number of simulated paths.
    n_steps : int or None
        Number of time steps per path. If None, use len(factors_hist).
    rng : np.random.Generator, optional
        Random generator.

    Returns
    -------
    np.ndarray
        Array of shape (n_paths, n_steps, k) with simulated factor returns.
    """
    if rng is None:
        rng = np.random.default_rng()
    X = factors_hist.dropna().values
    mu = X.mean(axis=0)
    cov = np.cov(X, rowvar=False)
    k = X.shape[1]
    if n_steps is None:
        n_steps = X.shape[0]
    L = np.linalg.cholesky(cov)
    z = rng.normal(size=(n_paths, n_steps, k))
    sims = mu + z @ L.T
    return sims


def simulate_private_paths(factors_hist: pd.DataFrame,
                           betas: pd.Series,
                           eps_sigma: float = 0.0,
                           n_paths: int = 10000,
                           n_steps: int | None = None,
                           rng: np.random.Generator | None = None) -> pd.DataFrame:
    """Simulate private-asset return paths by simulating factors then applying betas.

    Returns a DataFrame of shape (n_paths, n_steps) with simulated returns.
    """
    from .unified_model import FACTOR_ORDER

    if rng is None:
        rng = np.random.default_rng()
    sims_F = simulate_factors_normal(factors_hist[FACTOR_ORDER], n_paths=n_paths,
                                     n_steps=n_steps, rng=rng)
    k = sims_F.shape[2]
    beta_vec = betas.reindex(FACTOR_ORDER).values.reshape(k, 1)
    mean_part = sims_F @ beta_vec  # (n_paths, n_steps, 1)
    if eps_sigma > 0.0:
        eps = rng.normal(0.0, eps_sigma, size=mean_part.shape)
        total = mean_part + eps
    else:
        total = mean_part
    total = total.squeeze(-1)
    # Construct index: path 0..n_paths-1, time 0..n_steps-1
    idx = pd.Index(range(total.shape[0]), name="path")
    cols = pd.Index(range(total.shape[1]), name="step")
    return pd.DataFrame(total, index=idx, columns=cols)

