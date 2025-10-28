"""
De-smoothing module for fund returns with autocorrelation.

Implements Geltner (1993) de-smoothing for returns that exhibit spurious
autocorrelation due to stale pricing or appraisal methods.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, Optional, TYPE_CHECKING
from prelim_diagnostics import test_ar1_autocorrelation, print_ar1_diagnostics

if TYPE_CHECKING:
    from .checkpoints import CheckpointRunner


def geltner_desmooth(returns: pd.Series, ar1_coef: float) -> pd.Series:
    """
    De-smooth returns using Geltner (1993) method.

    The Geltner method assumes observed returns follow:
        R_observed(t) = θ * R_observed(t-1) + (1-θ) * R_true(t)

    Where θ is the smoothing parameter (AR1 coefficient).

    Solving for true returns:
        R_true(t) = [R_observed(t) - θ * R_observed(t-1)] / (1 - θ)

    Args:
        returns: Original (smoothed) return series
        ar1_coef: AR(1) coefficient from autocorrelation test

    Returns:
        De-smoothed return series with same index as input

    Reference:
        Geltner, D. (1993). "Estimating Market Values from Appraised Values
        without Assuming an Efficient Market." Journal of Real Estate Research.
    """
    if ar1_coef <= 0 or ar1_coef >= 1:
        raise ValueError(f"AR(1) coefficient must be in (0, 1), got {ar1_coef}")

    returns_clean = returns.dropna()

    # Calculate de-smoothed returns
    # First observation: use observed return (no lag available)
    desmoothed = pd.Series(index=returns_clean.index, dtype=float)
    desmoothed.iloc[0] = returns_clean.iloc[0]

    # Subsequent observations: apply Geltner formula
    for t in range(1, len(returns_clean)):
        r_obs_t = returns_clean.iloc[t]
        r_obs_t_lag = returns_clean.iloc[t-1]
        r_true_t = (r_obs_t - ar1_coef * r_obs_t_lag) / (1 - ar1_coef)
        desmoothed.iloc[t] = r_true_t

    return desmoothed


def desmooth_if_needed(
    returns: pd.Series,
    significance_level: float = 0.05,
    verbose: bool = True,
    checkpoint_runner: Optional['CheckpointRunner'] = None
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Test for AR(1) autocorrelation and de-smooth if significant.

    Args:
        returns: Fund return series
        significance_level: p-value threshold for AR(1) significance
        verbose: Print diagnostic information
        checkpoint_runner: Optional CheckpointRunner for human-in-the-loop interaction.
            If provided and interactive mode enabled, user will be prompted before
            applying de-smoothing. If None, proceeds automatically based on test results.

    Returns:
        Tuple of:
            - de-smoothed (or original) returns
            - diagnostics dict with test results and actions taken

    Note:
        Backward compatible: Works identically when checkpoint_runner=None.
    """
    # Test for AR(1) autocorrelation
    ar_test = test_ar1_autocorrelation(returns, significance_level, verbose=verbose)

    diagnostics = {
        "desmoothing_enabled": True,
        "desmoothing_examined": True,
        "ar1_test": ar_test,
        "desmoothed": False,
        "original_returns": returns.copy()
    }

    if verbose:
        print_ar1_diagnostics(ar_test, significance_level)

    # === CHECKPOINT: Human-in-the-loop decision (if enabled) ===
    if checkpoint_runner and ar_test['requires_desmoothing']:
        try:
            decision = checkpoint_runner.run_checkpoint(
                checkpoint_name="checkpoint-post-diagnostics",
                context={"ar_test": ar_test}
            )

            if decision == "no":
                print("⚠ Skipping de-smoothing per user request.")
                diagnostics['user_override'] = True
                diagnostics['user_decision'] = 'skip_desmoothing'
                return returns, diagnostics

        except Exception as e:
            # Graceful degradation if checkpoint fails
            if verbose:
                print(f"⚠ Checkpoint failed: {e}. Proceeding with default behavior.")
    # === END CHECKPOINT ===

    # De-smooth if needed
    if ar_test['requires_desmoothing']:
        if verbose:
            print(f"\nApplying Geltner (1993) de-smoothing...")

        desmoothed_returns = geltner_desmooth(returns, ar_test['ar1_coef'])
        diagnostics['desmoothed'] = True
        diagnostics['desmoothed_returns'] = desmoothed_returns

        # Calculate impact metrics
        original_vol = returns.std()
        desmoothed_vol = desmoothed_returns.std()
        vol_increase = (desmoothed_vol / original_vol - 1) * 100

        # Re-test de-smoothed returns
        retest = test_ar1_autocorrelation(desmoothed_returns, significance_level)
        diagnostics['retest'] = retest

        if verbose:
            print(f"\nDe-smoothing Results:")
            print(f"  Original volatility: {original_vol:.6f}")
            print(f"  De-smoothed volatility: {desmoothed_vol:.6f}")
            print(f"  Volatility increase: {vol_increase:+.2f}%")
            print(f"  New AR(1) coefficient: {retest['ar1_coef']:.6f}")
            print(f"  New AR(1) p-value: {retest['ar1_pvalue']:.6f}")

            if retest['is_significant']:
                print("  ⚠ Warning: Significant autocorrelation remains after de-smoothing")
            else:
                print("  ✓ Autocorrelation successfully removed")

        return desmoothed_returns, diagnostics

    else:
        return returns, diagnostics


def compare_smoothed_vs_desmoothed(
    returns_original: pd.Series,
    returns_desmoothed: pd.Series
) -> pd.DataFrame:
    """
    Compare properties of original vs de-smoothed returns.

    Args:
        returns_original: Original return series
        returns_desmoothed: De-smoothed return series

    Returns:
        DataFrame with comparative statistics
    """
    stats = []

    for name, returns in [("Original", returns_original), ("De-smoothed", returns_desmoothed)]:
        returns_clean = returns.dropna()

        # Calculate statistics
        mean_ret = returns_clean.mean()
        vol = returns_clean.std()
        sharpe = mean_ret / vol if vol > 0 else np.nan

        # AR(1) test
        ar_test = test_ar1_autocorrelation(returns_clean)

        stats.append({
            "Series": name,
            "Mean": mean_ret,
            "Volatility": vol,
            "Sharpe": sharpe,
            "AR(1)": ar_test['ar1_coef'],
            "AR(1) p-value": ar_test['ar1_pvalue'],
            "Skewness": returns_clean.skew(),
            "Kurtosis": returns_clean.kurtosis()
        })

    return pd.DataFrame(stats)
