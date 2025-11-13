# Black–Litterman Integration

The unified factor model can be embedded in a **Black–Litterman (BL)** framework to
form return expectations and optimise portfolios including Buyout and VC.

## 1. From Factors to Asset Expected Returns

Suppose we have:

- Factor premia \( \pi_F = \mathbb{E}[F_t] \) (long‑run expected returns for SC, CS, INNOV, TAIL).
- Factor loadings \( \beta^{asset} \) for each asset (public and private).

We form the prior expected return for asset \( i \):

\[
\mu_i^{prior} = \beta_i^\top \pi_F.
\]

This yields prior expected returns for:

- public equity portfolios,
- Buyout PE,
- VC,
- other asset classes that can be mapped into the factor space.

## 2. Investor Views

Views can be expressed:

- directly on **asset returns** (e.g. “Buyout PE will outperform SC by 300 bps”),
- or on **factor premia** (e.g. “Innovation premium will be lower than history”).

BL then blends:

- the equilibrium implied by the factor model and market data,
- the investor views, with confidence weights.

## 3. Advantages of the Unified Factor Approach

Because Buyout and VC share the same factor set as public equities:

- Views on **SC, CS, INNOV, TAIL** propagate naturally across public and private assets.
- The model is **internally consistent**:
  - If you believe innovation premium will compress, both VC and tech‑heavy public equities are affected.
  - If you believe spreads will widen structurally, Buyout and private credit are affected more than broad equities.

This creates a **single, coherent language** for expressing and implementing multi‑asset views.
