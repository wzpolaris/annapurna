# Executive Summary

This white paper describes a unified structural risk model for private markets, focused on
Buyout Private Equity (PE) and Venture Capital (VC). The model is designed primarily for
**risk analytics**, not performance attribution in the narrow sense.

We model both Buyout and VC as exposures to the same four **market-observable factors**:

- **SC** – small‑cap equity returns (public‑market analog to private portfolio companies)
- **CS** – credit spread changes (high‑yield or loan market stress)
- **INNOV** – innovation / technology cycle (e.g. Nasdaq minus small‑cap)
- **TAIL** – downside tail risk, derived from positive VIX changes

Returns for a generic private asset are written as:

\[
r^{Priv}_t = \beta_{SC} SC_t + \beta_{CS} CS_t + \beta_{INNOV} INNOV_t + \beta_{TAIL} TAIL_t + \varepsilon_t.
\]

Buyout and VC differ not by factor set, but by **beta magnitudes**:

- Buyout: high SC, moderate CS, small INNOV, moderate–high TAIL
- VC: moderate SC, small–moderate CS, high INNOV, high TAIL

This produces:

- **Theoretical consistency** – matches factor‑based no‑arbitrage thinking (APT / SDF)
- **Clean implementation** – one factor system, different betas
- **Robust risk decomposition** – common factors across strategies
- **Ease of explanation** – simple story for IC / board audiences
- **Compatibility with Black–Litterman** – factors map cleanly into a multi‑asset view system
- **Fund‑specific customization** – overlays adjust betas for sector, geography, strategy, etc.

The model’s primary uses are:

1. Constructing **factor‑based covariance matrices** for Buyout and VC.
2. Aggregating bottom‑up fund exposures into portfolio‑level factor risk.
3. Running **Monte Carlo simulations** at the factor level, then mapping into private returns.
4. Comparing Buyout / VC risk (e.g. VaR, CVaR, tail loss) against public equity benchmarks.
5. Supporting a **Black–Litterman** overlay where views on private premia are expressed
   relative to public factor premia.

Fund‑level appraisal returns (if available) can be used as a **desmoothed overlay**:
we estimate betas from desmoothed series and shrink them toward the structural betas
defined by this model.
