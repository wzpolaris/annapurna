# Beta Assignment & Interpretation

## 1. Role of Structural Betas

The betas \( \beta \) are **structural parameters** that connect public, liquid factor
returns to private asset class behavior. They serve three purposes:

1. Define the **shape of risk** for Buyout and VC.
2. Map factor shocks into private returns for **scenario and Monte Carlo analysis**.
3. Provide a prior (or anchor) for fund‑specific beta estimates from desmoothed appraisal data.

We distinguish between:

- **Structural betas** – deduced from theory and broad empirical evidence.
- **Fund betas** – estimated from specific fund histories (after desmoothing).
- **Blended betas** – a shrinkage combination of structural and fund betas, when fund data exists.

## 2. Typical Beta Ranges

### 2.1 Buyout PE (BO)

A typical Buyout exposure profile:

- \( \beta^{BO}_{SC} \in [1.3, 1.8] \)
- \( \beta^{BO}_{CS} \in [0.6, 1.0] \)
- \( \beta^{BO}_{INNOV} \in [0.0, 0.2] \)
- \( \beta^{BO}_{TAIL} \in [1.0, 1.5] \)

Interpretation:

- **SC**: Leveraged small‑cap beta (financial and operating leverage).
- **CS**: Sensitivity to credit conditions and refinancing risk.
- **INNOV**: Usually small; may increase for tech‑heavy buyout strategies.
- **TAIL**: Larger losses than implied by linear beta alone, due to leverage and exit constraints.

### 2.2 Venture Capital (VC)

A typical VC exposure profile:

- \( \beta^{VC}_{SC} \in [1.0, 1.4] \)
- \( \beta^{VC}_{CS} \in [0.2, 0.6] \)
- \( \beta^{VC}_{INNOV} \in [0.8, 1.4] \)
- \( \beta^{VC}_{TAIL} \in [1.5, 2.5] \)

Interpretation:

- **SC**: General equity sensitivity (risk‑on / risk‑off).
- **CS**: Funding and liquidity conditions; weaker than Buyout but non‑zero.
- **INNOV**: Main driver – tech and innovation cycles.
- **TAIL**: VC valuations fall sharply when exit markets close; high tail beta.

## 3. How Betas Are Chosen in Practice

In a practical implementation, we recommend:

1. **Start from structural priors** as above.
2. If fund appraisal data exist:
   - Desmooth returns (AR(1) inversion or kernel method).
   - Regress desmoothed returns on the four factors.
   - Obtain fund‑level beta estimates \( \hat{\beta}^{fund} \).
3. Form **blended betas**:
   \[
   \beta^{blend} = \lambda \hat{\beta}^{fund} + (1 - \lambda) \beta^{struct},
   \]
   with \( \lambda \in [0, 1] \) chosen based on:
   - length of fund history,
   - degree of smoothing,
   - stability of estimated betas,
   - qualitative comfort with fund‑specific behavior.

For risk analytics at the **asset‑class level**, the structural betas alone
are often sufficient; blended betas are most useful for **fund‑by‑fund** reporting.
