"""
Preliminary diagnostics for fund returns before RBSA analysis.

Includes autocorrelation testing and de-smoothing recommendations.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, Any
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.stats.diagnostic import acorr_ljungbox


def test_ar1_autocorrelation(returns: pd.Series, significance_level: float = 0.05, verbose: bool = False) -> Dict[str, Any]:
    """
    Test if returns exhibit significant AR(1) autocorrelation.

    Args:
        returns: Time series of returns
        significance_level: p-value threshold for significance (default 0.05)
        verbose: Print diagnostic information

    Returns:
        Dict with:
            - ar1_coef: AR(1) coefficient (ρ)
            - ar1_pvalue: p-value for AR(1) coefficient
            - is_significant: True if coefficient is statistically significant
            - ljungbox_pvalue: Ljung-Box test p-value for lag 1
            - requires_desmoothing: True if significant autocorrelation detected
            - error: Error message if test failed
    """
    # Remove NaN values
    returns_clean = returns.dropna()

    if len(returns_clean) < 10:
        error_msg = f"Insufficient data: {len(returns_clean)} obs (need ≥10)"
        if verbose:
            print(f"⚠ AR(1) test skipped: {error_msg}")
        return {
            "ar1_coef": 0.0,  # Use 0 instead of nan when insufficient data
            "ar1_pvalue": 1.0,  # High p-value = not significant
            "is_significant": False,
            "ljungbox_pvalue": 1.0,
            "requires_desmoothing": False,
            "n_obs": len(returns_clean),
            "error": error_msg
        }

    # Fit AR(1) model
    try:
        model = AutoReg(returns_clean, lags=1, trend='c')
        result = model.fit()

        # TODO: remove commented out section if not needed
        # if verbose:
        #     print(f"\nAR(1) Model Fit:")
        #     print(f"  Parameters: {list(result.params.index)}")
        #     print(f"  Coefficients: {result.params.values}")

        # Extract AR(1) coefficient and p-value
        # Try multiple possible parameter names
        # ar1_coef = None
        # ar1_pvalue = None
        # # Check all parameter names for lag-1
        # for param_name in result.params.index:
        #     if 'L1' in str(param_name) or '.1' in str(param_name):
        #         ar1_coef = result.params[param_name]
        #         ar1_pvalue = result.pvalues[param_name]
        #         if verbose:
        #             print(f"  Found AR(1) coefficient in parameter: {param_name}")
        #         break

        # Get the endog variable name from the model
        base_name = model.endog_names  # or returns_clean.name
        lag_param_name = f"{base_name}.L1"  # Construct the exact parameter name

        ar1_coef = result.params[lag_param_name]
        ar1_pvalue = result.pvalues[lag_param_name]


        if ar1_coef is None:
            error_msg = f"Could not find AR(1) lag coefficient. Available: {list(result.params.index)}"
            if verbose:
                print(f"⚠ {error_msg}")
            return {
                "ar1_coef": 0.0,
                "ar1_pvalue": 1.0,
                "is_significant": False,
                "ljungbox_pvalue": np.nan,
                "requires_desmoothing": False,
                "n_obs": len(returns_clean),
                "error": error_msg
            }

        # Ljung-Box test for autocorrelation at lag 1
        lb_result = acorr_ljungbox(returns_clean, lags=[1], return_df=True)
        lb_pvalue = lb_result['lb_pvalue'].iloc[0]

        # Determine if de-smoothing is needed
        # Criteria: AR(1) coefficient is significant AND positive
        is_significant = (ar1_pvalue < significance_level) and (ar1_coef > 0)

        result_dict = {
            "ar1_coef": float(ar1_coef),
            "ar1_pvalue": float(ar1_pvalue),
            "is_significant": is_significant,
            "ljungbox_pvalue": float(lb_pvalue),
            "requires_desmoothing": is_significant,
            "n_obs": len(returns_clean)
        }

        # if verbose:
        #     print(f"\nAR(1) Test Results:")
        #     print(f"  ρ = {ar1_coef:.6f} (p={ar1_pvalue:.6f})")
        #     print(f"  Ljung-Box p-value: {lb_pvalue:.6f}")
        #     print(f"  Significant: {is_significant}")

        return result_dict

    except Exception as e:
        error_msg = f"AR(1) model fitting failed: {str(e)}"
        if verbose:
            print(f"⚠ {error_msg}")
        return {
            "ar1_coef": 0.0,
            "ar1_pvalue": 1.0,
            "is_significant": False,
            "ljungbox_pvalue": np.nan,
            "requires_desmoothing": False,
            "n_obs": len(returns_clean),
            "error": error_msg
        }


def print_ar1_diagnostics(ar_test: Dict[str, Any], significance_level: float = 0.05) -> None:
    """
    Print formatted AR(1) test diagnostics.

    Args:
        ar_test: Results from test_ar1_autocorrelation()
        significance_level: Significance threshold used
    """
    print("\n" + "="*80)
    print("AR(1) AUTOCORRELATION TEST - Preliminary Diagnostics")
    print("="*80)
    print(f"Sample size: {ar_test.get('n_obs', 'N/A')} observations")

    if "error" in ar_test:
        print(f"⚠ ERROR: {ar_test['error']}")
        print("  Proceeding without de-smoothing")
        print("="*80)
        return

    ar1_coef = ar_test['ar1_coef']
    ar1_pvalue = ar_test['ar1_pvalue']
    lb_pvalue = ar_test['ljungbox_pvalue']

    print(f"AR(1) coefficient (ρ): {ar1_coef:.6f}")
    print(f"AR(1) p-value: {ar1_pvalue:.6f}")
    print(f"Ljung-Box p-value (lag 1): {lb_pvalue:.6f}")
    print(f"Significance level: {significance_level}")

    if ar_test['requires_desmoothing']:
        print(f"\n✓ SIGNIFICANT positive autocorrelation detected (ρ={ar1_coef:.4f}, p={ar1_pvalue:.4f})")
        print("  → De-smoothing recommended")
    else:
        if ar1_coef > 0 and ar1_pvalue >= significance_level:
            print(f"\n○ Positive autocorrelation (ρ={ar1_coef:.4f}) but NOT significant (p={ar1_pvalue:.4f})")
        elif ar1_coef <= 0:
            print(f"\n✓ No positive autocorrelation (ρ={ar1_coef:.4f})")
        else:
            print(f"\n✓ No significant autocorrelation detected")
        print("  → No de-smoothing needed")

    print("="*80)
