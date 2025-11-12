# --TURN--

delay = 3.0
cardType = "user-assistant"

userText = "Explain to me why the performance is misleading."

assistantBlocks_type = "markdown"
assistantBlocks_content = """

**General information on smoothing and appraisal bias...**

An issue with reported private equity returns is that they are appraisal-based, not transaction-based, and this results in artificially smooth time series. The smoothing then leads to several well-documented issues:
- Understatment of estimated volatility and true economic risk.
- Lower estimated correlations of PE with public markets.
- Masking of tail and liquidity risks, especially during crises

Technically speaking, smoothing is the result of "serial correlation" in the reported returns. So, a "de-smoothing" analytical adjustment is often applied to get a better estimate the true risk and return characteristics of PE investments.

Often a de-smoothing adjustment is applied on the Fund's reported returns if the time series is to be used in standard performance and risk analyses including scenario testing, optimization, etc.

I will apply the technique to the Hamilton Lane fund's returns.

---

Selected references related to the smoothing of returns:
- Sorensen & Jagannathan (2014) "The Public Market Equivalent and Private Equity Performance."
Netspar Discussion Paper, 09/2013-039.
- Ang, Andrew, Bingxu Chen, William N. Goetzmann, and Ludovic Phalippou.
"Estimating Private Equity Returns from Limited Partner Cash Flows."
Pacific-Basin Finance Journal 50 (2018): 96–118.
https://doi.org/10.1016/j.pacfin.2017.04.012

"""
