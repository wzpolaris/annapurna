"""Unified Buyout/VC factor model.

Provides utilities to:

- store / access structural betas for Buyout and VC;
- compute factor-implied returns;
- optionally add idiosyncratic noise for Monte Carlo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FACTOR_ORDER = ["SC", "CS", "INNOV", "TAIL"]


def get_structural_betas(strategy: str) -> pd.Series:
    """Return structural betas for a given strategy.

    Parameters
    ----------
    strategy : {"buyout", "vc"}
        Strategy name (case-insensitive).

    Returns
    -------
    Series
        Betas indexed by factor name.
    """
    s = strategy.lower()
    if s == "buyout":
        data = {"SC": 1.5, "CS": 0.8, "INNOV": 0.1, "TAIL": 1.2}
    elif s == "vc":
        data = {"SC": 1.2, "CS": 0.4, "INNOV": 1.1, "TAIL": 2.0}
    else:
        raise ValueError(f"Unknown strategy '{strategy}' (expected 'buyout' or 'vc').")
    return pd.Series(data)[FACTOR_ORDER]


def factor_returns_to_privates(factors: pd.DataFrame,
                               betas: pd.Series,
                               eps_sigma: float = 0.0,
                               rng: np.random.Generator | None = None) -> pd.Series:
    """Map factor returns to private returns via linear model plus optional noise.

    Parameters
    ----------
    factors : DataFrame
        Factor return DataFrame with columns matching FACTOR_ORDER.
    betas : Series
        Betas indexed by factor name (same order as FACTOR_ORDER).
    eps_sigma : float
        Idiosyncratic volatility (per period). If 0, no noise is added.
    rng : np.random.Generator, optional
        Random generator for noise.

    Returns
    -------
    Series
        Private asset return series.
    """
    X = factors[FACTOR_ORDER].dropna()
    beta_vec = betas.reindex(FACTOR_ORDER).values
    mean_part = X.values @ beta_vec
    idx = X.index
    if eps_sigma > 0.0:
        if rng is None:
            rng = np.random.default_rng()
        eps = rng.normal(0.0, eps_sigma, size=len(idx))
        vals = mean_part + eps
    else:
        vals = mean_part
    return pd.Series(vals, index=idx, name="Privates")

