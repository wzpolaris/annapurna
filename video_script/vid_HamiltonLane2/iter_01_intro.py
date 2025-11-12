# --TURN--

delay = 3.0
cardType = "assistant-only"
metadata = {'showUserText': False}

userText = "slides"

assistantBlocks_type = "markdown"
assistantBlocks_content = """

Welcome to the Northfield AI powered Analytics Engine.

How can I assist you?

"""


from backend.app.upload_block import upload_block_component

# --TURN--

delay = 2.0
pause = True

cardType = "user-assistant"

userText = "I want to analyze a specific PE fund"

assistantBlocks_type = "markdown"
assistantBlocks_content = "Ok. Provide me with whatever relevant information you have."

assistantBlocks_type = "upload"
assistantBlocks_content = upload_block_component()


# --TURN--

delay = 5.0
pause = True
cardType = "assistant-only"

#userText = "The factsheet has been uploaded."

assistantBlocks_type = "markdown"
assistantBlocks_content = """

Based on the fact sheet, here's what we're evaluating:

**Fund Structure:**
- **Type:** '40 Act Registered, Closed-End Non-Diversified Fund with Tender Offers
- **Manager:** Hamilton Lane Advisors, LLC
- **AUM:** $4.67 billion (as of August 31, 2025)
- **Inception:** September 2020 (as Evergreen Private Fund L.P.), converted January 2021
- **Strategy:** Direct co-investments (49%) and secondary transactions (51%) in private equity
- **Portfolio:** 157 investments across 153 general partners

"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Are there specific things you would like examine?
"""

# --TURN--

delay = 2.0
pause = True

cardType = "user-assistant"

userText = "performance and risk"

assistantBlocks_type = "markdown"
assistantBlocks_content = """
I have extracted returns for the Institutional(I) Shares. 
"""

assistantBlocks_type = "html"
assistantBlocks_content = """
<table style="font-size:.8em;">
  <thead>
    <tr>
      <th colspan="2" style="font-weight:normal; text-align:center;">Annual Return<br>Since Mar 2020<br>(Inception)</th>
    </tr>
  </thead>
  <tbody  >
    <tr>
      <td>Fund</td>
      <td style="text-align:center;">15.98</td>
    </tr>
    <tr>
      <td >MSCI</td>
      <td style="text-align:center;">12.89</td>
    </tr>
  </tbody>
</table>
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
While the reported performance is favorable compared to global equities, the monthly returns in the PDF appear to be significantly smoothed, and the series displays very low volatility.
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
This is a known issue with PE fund reporting, and it can lead to misleading conclusions if not properly addressed.
"""



# --TURN--

delay = 2.0
pause = True

cardType = "user-assistant"

userText = "How do you address?"

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