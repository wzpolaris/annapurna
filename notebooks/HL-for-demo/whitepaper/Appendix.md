# Appendix: Additional Details & Citations

This appendix summarises some practical and theoretical details that support the unified model.

## A. Factor Construction Notes

- Work at a **monthly frequency** to align with private appraisal data.
- Use **total returns** (including dividends) for SC and INNOV.
- For CS:
  - Prefer HY OAS changes if available.
  - Otherwise regress HY ETF returns on duration‑matched Treasury ETF returns and take the residual as the spread factor.
- For TAIL:
  - Standardise ΔVIX using a rolling mean and volatility.
  - Use \( TAIL_t = \log(1 + z_t^+) \) to avoid numerical dominance of extreme spikes.

## B. References (Indicative)

- Sorensen, M., & Jagannathan, R. (2014). *The Public Market Equivalent and Private Equity Performance.*
- Ang, A., Chen, B., Goetzmann, W., & Phalippou, L. (2018). *Estimating Private Equity Returns and Risk from Limited Partner Cash Flows.*
- Axelson, U., Jenkinson, T., Strömberg, P., & Weisbach, M. (2013). *Borrow Cheap, Buy High? The Determinants of Leverage and Pricing in Buyouts.*
- Harris, R., Jenkinson, T., & Kaplan, S. (2014). *Private Equity Performance: What Do We Know?*
- Nanda, R., & Rhodes‑Kropf, M. (2013). *Investment Cycles and Startup Innovation.*
- Pástor, L., & Veronesi, P. (2009, 2012). *Technological Revolutions and Stock Prices; Uncertainty about Long‑Run Growth.*
- Kelly, B., Jiang, H., & Xiu, D. (2019). *Measuring Tail Risk.*

These and related papers motivate:

- the use of public‑market factors to infer private risk,
- the importance of credit cycles for Buyout PE,
- the link between innovation cycles and VC,
- the non‑linear nature of tail risk in private assets.
