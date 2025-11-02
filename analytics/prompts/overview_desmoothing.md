# De-smoothing Fund Returns

## Overview

Some fund returns exhibit **spurious autocorrelation** due to:
- **Stale pricing** (illiquid assets marked at previous prices)
- **Appraisal-based valuations** (real estate, private equity)
- **Smoothed NAV calculations** (certain hedge fund strategies)

This artificially reduces measured volatility and creates misleading correlations with liquid benchmark indices. The de-smoothing process corrects this by recovering the "true" unsmoothed return series.

## When De-smoothing is Applied

The pipeline automatically:
1. Tests fund returns for AR(1) autocorrelation
2. If significant positive autocorrelation is detected (p < 0.05), applies Geltner (1993) de-smoothing
3. Verifies autocorrelation is removed after de-smoothing

## Statistical Test

### AR(1) Model
```
R(t) = α + ρ * R(t-1) + ε(t)
```

Where:
- **ρ** (rho) is the AR(1) coefficient
- **Significant** if p-value < 0.05 (default threshold)
- **Positive** autocorrelation (ρ > 0) indicates smoothing

### Ljung-Box Test
Complementary test for autocorrelation at lag 1:
- **H₀**: No autocorrelation
- **Reject H₀** if p-value < 0.05

## De-smoothing Method: Geltner (1993)

### Smoothing Model
Observed returns are assumed to follow:
```
R_observed(t) = θ * R_observed(t-1) + (1 - θ) * R_true(t)
```

Where **θ** (theta) is the smoothing parameter, estimated by the AR(1) coefficient.

### Recovery Formula
True (unsmoothed) returns are recovered by:
```
R_true(t) = [R_observed(t) - θ * R_observed(t-1)] / (1 - θ)
```

### Properties
- **Increases volatility**: De-smoothed returns have higher standard deviation
- **Removes autocorrelation**: AR(1) coefficient should become insignificant
- **Preserves mean**: Average return is unchanged (approximately)
- **First observation**: Uses observed return (no lag available)

## Configuration

In `config.yaml`:

```yaml
preprocessing:
  desmooth:
    enabled: true           # Set to false to disable
    significance_level: 0.05  # p-value threshold for AR(1) test
    verbose: true           # Print detailed diagnostics
```

### Parameters
- **enabled**: Enable/disable de-smoothing (default: true)
- **significance_level**: p-value threshold for determining if AR(1) coefficient is significant
  - 0.05 = 95% confidence (standard)
  - 0.01 = 99% confidence (more conservative)
  - 0.10 = 90% confidence (more aggressive)
- **verbose**: Print AR(1) test results and de-smoothing diagnostics

## Example Output

### Case 1: No Smoothing Detected
```
================================================================================
AR(1) AUTOCORRELATION TEST
================================================================================
Sample size: 221 observations
AR(1) coefficient: 0.023456
AR(1) p-value: 0.734120
Ljung-Box p-value (lag 1): 0.698234
Significance level: 0.05

✓ No significant autocorrelation detected
  Proceeding with original returns (no de-smoothing needed)
================================================================================
```

### Case 2: Smoothing Detected and Corrected
```
================================================================================
AR(1) AUTOCORRELATION TEST
================================================================================
Sample size: 221 observations
AR(1) coefficient: 0.247831
AR(1) p-value: 0.000234
Ljung-Box p-value (lag 1): 0.000189
Significance level: 0.05

✓ Significant positive autocorrelation detected (ρ=0.2478, p=0.0002)
  Applying Geltner (1993) de-smoothing...

De-smoothing Results:
  Original volatility: 0.012345
  De-smoothed volatility: 0.015678
  Volatility increase: +27.03%
  New AR(1) coefficient: 0.018234
  New AR(1) p-value: 0.821456
  ✓ Autocorrelation successfully removed
================================================================================
```

## Impact on RBSA Results

### Before De-smoothing (Smoothed Returns)
- **Lower volatility**: Fund appears less risky
- **Higher R²**: Spurious correlation with liquid indices
- **Autocorrelated residuals**: Violates OLS assumptions
- **Biased standard errors**: Underestimated coefficient uncertainty

### After De-smoothing (True Returns)
- **Higher volatility**: Reflects actual risk
- **Lower R²**: Realistic explanatory power
- **Independent residuals**: Valid regression assumptions
- **Correct standard errors**: Proper inference

### Asset Weight Changes
De-smoothing typically results in:
- **Less weight** on highly liquid assets (SPY, IEF)
- **More weight** on alternative assets that match fund's true volatility
- **Different factor exposures**: More accurate style classification

## Technical Notes

### Why AR(1)?
- First-order autocorrelation is sufficient for most smoothing mechanisms
- Higher-order models (AR(2), AR(3)) rarely improve diagnosis
- Ljung-Box test provides additional confirmation

### Limitations
- Assumes **linear** smoothing process
- Requires **minimum 10 observations** (preferably 30+)
- Does not handle **time-varying** smoothing
- Cannot detect **look-ahead bias** or other data issues

### Alternative Methods
- **Getmansky et al. (2004)**: Maximum likelihood estimation with moving average smoothing
- **Dimson (1979)**: Aggregated coefficients method for beta estimation
- Current implementation uses **Geltner** for simplicity and speed

## References

1. **Geltner, D. (1993)**. "Estimating Market Values from Appraised Values without Assuming an Efficient Market." *Journal of Real Estate Research*, 8(3), 325-345.

2. **Getmansky, M., Lo, A. W., & Makarov, I. (2004)**. "An Econometric Model of Serial Correlation and Illiquidity in Hedge Fund Returns." *Journal of Financial Economics*, 74(3), 529-609.

3. **Dimson, E. (1979)**. "Risk Measurement When Shares Are Subject to Infrequent Trading." *Journal of Financial Economics*, 7(2), 197-226.

## FAQ

**Q: Should I always enable de-smoothing?**
A: Yes, unless you know your fund returns are not smoothed. The test is automatic and only applies de-smoothing if significant autocorrelation is detected.

**Q: What if de-smoothing fails to remove autocorrelation?**
A: This suggests more complex smoothing (e.g., MA process) or genuine momentum. Consider manual investigation or alternative methods (Getmansky et al.).

**Q: Can de-smoothing create negative returns where there were none?**
A: Yes, de-smoothing can amplify losses. This is correct—smoothing artificially dampens drawdowns.

**Q: Does de-smoothing affect the benchmark returns (X)?**
A: No, only fund returns (y) are de-smoothed. Liquid ETF benchmarks should not exhibit smoothing.

**Q: What if my fund has only 36 months of data?**
A: De-smoothing still works, but AR(1) estimates are less precise. Consider increasing `significance_level` to 0.10 for small samples.
