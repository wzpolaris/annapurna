
Based on the formula in formulas.md and the detailed analysis report, here's a short description of each factor in the structural model:

## Structural Model Factors

**Model:** $r_{PE_t} = \beta_{GSC_t} GSC_t + \beta_{SPRD_t} SPRD_t + \beta_{INNOV_t} INNOV_t + \beta_{TAIL_t} TAIL_t + \epsilon_{t}$

(Note: The documentation uses **SC, CS, INNOV, TAIL** - where SC appears to be the same as GSC, and CS appears to be the same as SPRD)

### **SC (Small Cap / Global Small Cap)**
- **Market factor** representing small-cap equity exposure
- Captures linear market risk and equity sensitivity
- HLPAF beta: ~0.11 (calibrated), ~1.63 (structural)
- Contributes ~4.5% of total variance
- Mean monthly return: 0.83%

### **CS (Credit Spread)**
- **Credit risk factor** measuring corporate credit conditions
- Reflects stress in credit markets and funding costs
- HLPAF beta: ~0.05 (calibrated), ~0.76 (structural)
- Contributes <1% of total variance
- Mean monthly return: 0.04%

### **INNOV (Innovation)**
- **Growth/tech factor** capturing innovation-driven returns
- Exposure to technology and growth sectors
- HLPAF beta: ~0.03 (calibrated), ~0.41 (structural)
- Slightly negative variance contribution (acts as minor hedge)
- Mean monthly return: 0.62%

### **TAIL (VIX / Crisis Factor)**
- **Non-linear crisis exposure** from volatility spikes (VIX)
- Captures illiquidity, leverage, and operational stress during market crises
- **Dominant risk source**: contributes ~95% of HLPAF variance
- HLPAF beta: ~0.23 (calibrated), ~3.25 (structural)
- Mean monthly factor value: -22.9% (highly negative during crises)
- Low correlation with S&P 500 (-0.07) creates non-linear, non-hedgeable downside risk
