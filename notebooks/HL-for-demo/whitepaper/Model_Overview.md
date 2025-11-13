# Structural Factor Model

## 1. Unified Factor Representation

We use a single, unified factor representation for both Buyout PE and VC:

\[
r^{Priv}_t = \beta_{SC} \cdot SC_t
            + \beta_{CS} \cdot CS_t
            + \beta_{INNOV} \cdot INNOV_t
            + \beta_{TAIL} \cdot TAIL_t
            + \varepsilon_t.
\]

Where:

- \( SC_t \) = small‑cap equity total return (e.g. monthly log‑return of a global small‑cap ETF)
- \( CS_t \) = credit spread factor (change in HY OAS, or HY vs Treasury residual)
- \( INNOV_t \) = innovation / technology cycle factor
- \( TAIL_t \) = tail‑risk factor, from positive VIX changes
- \( \varepsilon_t \) = idiosyncratic (specific) component

For Buyout and VC we write, explicitly:

\[
\begin{aligned}
r^{BO}_t &= \beta^{BO}_{SC} SC_t + \beta^{BO}_{CS} CS_t + \beta^{BO}_{INNOV} INNOV_t + \beta^{BO}_{TAIL} TAIL_t + \varepsilon^{BO}_t, \\
r^{VC}_t &= \beta^{VC}_{SC} SC_t + \beta^{VC}_{CS} CS_t + \beta^{VC}_{INNOV} INNOV_t + \beta^{VC}_{TAIL} TAIL_t + \varepsilon^{VC}_t.
\end{aligned}
\]

The **factor set is identical**, but \( \beta^{BO} \) and \( \beta^{VC} \) differ.

## 2. Factors as Market‑Observable Index Proxies

We choose factors so that each can be proxied with a **liquid, tradable time series**:

- **SC** – Small‑cap equity
  - US: IWM (Russell 2000)
  - Global: VSS or a composite of regional small‑cap ETFs
- **CS** – Credit spreads
  - HY OAS from FRED, or
  - Residual from regressing HY ETF (HYG) on Treasury ETF (IEF)
- **INNOV** – Innovation / tech cycle
  - 6‑month moving average of (Nasdaq 100 – Russell 2000) excess return
- **TAIL** – Tail risk
  - \( TAIL_t = \log(1 + z_t^+) \), where \( z_t \) is standardized ΔVIX and \(z_t^+ = \max(z_t, 0)\)

These are constructed at a **monthly** frequency for stability and to match private appraisal intervals.

## 3. Interpretation by Strategy

- **Buyout PE**
  - SC_t: captures the operating and valuation cyclicality of mid‑market companies
  - CS_t: captures debt market conditions and refinancing risk
  - INNOV_t: small exposure unless the fund is heavily tech‑tilted
  - TAIL_t: captures amplified drawdowns during crises

- **Venture Capital**
  - SC_t: general equity market sensitivity
  - CS_t: funding‑environment dependence (less than Buyout)
  - INNOV_t: central driver (IPO waves, tech cycles, intangible capital shocks)
  - TAIL_t: large drawdown sensitivity when exit markets freeze

This structure allows both strategies to be described in a consistent language while
highlighting their differences through the size of their betas.
