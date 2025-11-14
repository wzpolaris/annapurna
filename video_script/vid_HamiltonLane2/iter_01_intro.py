# --TURN--

delay = 3.0
cardType = "assistant-only"
metadata = {'showUserText': False}

userText = "slides"

assistantBlocks_type = "markdown"
assistantBlocks_content = """

Welcome to Lumenta\n
\n
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

Based on the fact sheet, we are analyzing the following PE fund:

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
Reported performance is favorable compared to global equities.
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
However, the monthly returns have been highly smoothed, with extremely low volatility that is not realistic.
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
As you know, this is a well documented issue with PE fund reporting
- Leads to wildly misleading conclusions if not properly addressed.
- [Desmoothing technique](?drawer=desmooth.html) techniques can be applied to attempt to undo the smoothing effects.
"""

