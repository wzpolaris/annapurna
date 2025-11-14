# HLPAF Analysis Report
**Generated:** 2025-11-13 19:01:02
**Source Notebook:** `07_HLPAF_Analysis.ipynb`
---
# Notebook 6 – Hamilton Lane Private Assets Fund (HLPAF) Analysis

This notebook applies the unified structural model to Hamilton Lane Private Assets Fund,
using:
- reported Class R monthly returns from the fact sheet,
- portfolio composition (strategy, sector, geography, investment type),
- the SC/CS/INNOV/TAIL factor set.

## 1. Enter HLPAF Class R Monthly Returns (from Fact Sheet)
Returns are in percent; we convert to decimal.

### Basic Summary Statistics
### Plot Monthly Returns and Cumulative NAV
## 2. Desmoothing via AR(1)
Estimate AR(1) via proper OLS regression and construct an "unsmoothed" return series.

### Compare original vs desmoothed distributions
## 3. Build HLPAF Structural Betas via Overlays
Use unified structural betas and overlay functions.

### 3.1 Strategy Mix Overlay (Buyout / VC)

### 3.2 Sector Overlay (29% Tech)

### 3.3 Geography Overlay (71% NA, 22% EU, 3% APAC, 4% ROW)

### 3.4 Investment Type Overlay (co-invest & GP-led concentration)

## 4. Regress HLPAF Desmoothed Returns on Factors (Optional)
This assumes you have built real factors (SC, CS, INNOV, TAIL) as `factors_real`.

## 5. Compare HLPAF vs S&P 500 in Factor Space

## 6. Monte Carlo Comparison – HLPAF vs S&P 500
Using the estimated/structural betas, simulate distributions and compare VaR/CVaR.

## Export Notebook to Markdown

Generate a comprehensive markdown report with all outputs.
