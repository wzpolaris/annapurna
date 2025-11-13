"""Fund-specific overlay utilities.

Overlays adjust structural betas based on:

- strategy mix (e.g. % buyout vs % VC),
- sector tilt (e.g. overweight tech),
- geography (e.g. NA vs Europe),
- investment type (e.g. GP-led single-asset vs diversified LP-led).

The goal is to keep the core factor set fixed (SC, CS, INNOV, TAIL) and
apply simple, transparent multipliers to betas to reflect fund characteristics.
"""

from __future__ import annotations

import pandas as pd


def strategy_mix_overlay(beta_buyout: pd.Series,
                         beta_vc: pd.Series,
                         w_buyout: float,
                         w_vc: float) -> pd.Series:
    """Blend Buyout and VC betas according to a strategy mix.

    Parameters
    ----------
    beta_buyout : Series
        Structural Buyout betas.
    beta_vc : Series
        Structural VC betas.
    w_buyout : float
        Weight on Buyout strategy (e.g. 0.7).
    w_vc : float
        Weight on VC strategy (e.g. 0.3).

    Returns
    -------
    Series
        Blended betas for the strategy mix.
    """
    w_sum = w_buyout + w_vc
    if w_sum <= 0:
        raise ValueError("w_buyout + w_vc must be positive.")
    wb = w_buyout / w_sum
    wv = w_vc / w_sum
    return wb * beta_buyout + wv * beta_vc


def sector_overlay(betas: pd.Series,
                   tech_weight: float,
                   baseline_tech_weight: float = 0.2,
                   max_innov_scale: float = 2.0) -> pd.Series:
    """Adjust INNOV and TAIL betas based on tech sector weight.

    Parameters
    ----------
    betas : Series
        Base betas.
    tech_weight : float
        Fund's tech / IT sector weight (0-1).
    baseline_tech_weight : float
        Baseline tech weight where no adjustment is applied.
    max_innov_scale : float
        Maximum multiplicative scale to INNOV beta when tech_weight is 100%.

    Returns
    -------
    Series
        Adjusted betas.
    """
    adj = betas.copy()
    # linear scale factor relative to baseline
    if tech_weight <= 0:
        scale = 0.8  # very low tech: slightly reduce INNOV/TAIL
    else:
        rel = tech_weight / max(baseline_tech_weight, 1e-6)
        scale = 1.0 + (max_innov_scale - 1.0) * min(rel, 1.5) / 1.5
    if "INNOV" in adj.index:
        adj["INNOV"] *= scale
    if "TAIL" in adj.index:
        adj["TAIL"] *= (0.5 * scale + 0.5)  # smaller adjustment on TAIL
    return adj


def geography_overlay(betas: pd.Series,
                      na_weight: float,
                      eu_weight: float,
                      apac_weight: float,
                      row_weight: float) -> pd.Series:
    """Placeholder geography overlay.

    For now this simply rescales SC beta slightly based on NA vs non-NA exposure,
    assuming NA small caps have a bit more cyclicality than a diversified global mix.

    Parameters
    ----------
    betas : Series
        Base betas.
    na_weight, eu_weight, apac_weight, row_weight : float
        Region weights (0-1).

    Returns
    -------
    Series
        Adjusted betas.
    """
    adj = betas.copy()
    total = na_weight + eu_weight + apac_weight + row_weight
    if total <= 0:
        return adj
    na_share = na_weight / total
    # modestly bump SC when North America dominates
    if "SC" in adj.index:
        adj["SC"] *= (0.9 + 0.3 * na_share)
    return adj


def investment_type_overlay(betas: pd.Series,
                            concentration_level: float) -> pd.Series:
    """Adjust TAIL beta based on deal concentration / GP-led vs LP-led.

    Parameters
    ----------
    betas : Series
        Base betas.
    concentration_level : float
        0 => highly diversified LP-led secondary;
        1 => concentrated GP-led single-asset / co-invest.

    Returns
    -------
    Series
        Adjusted betas.
    """
    adj = betas.copy()
    scale = 1.0 + 1.0 * min(max(concentration_level, 0.0), 1.0)
    if "TAIL" in adj.index:
        adj["TAIL"] *= scale
    return adj
