TURNS = [
    {
        "delay": 3.0,
        "cardType": "assistant-only",
        "metadata": {'showUserText': False},
        "userText": "slides",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """Welcome to the Northfield AI powered Analytics Engine.
How can I assist you?
""",
            },
        ],
    },
    {
        "delay": 2.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "I want to analyze a specific PE fund",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """Ok. Provide me with whatever relevant information you have.""",
            },
            {
                "type": "upload",
                "content": """upload_block_component()""",
            },
        ],
    },
    {
        "delay": 5.0,
        "pause": True,
        "cardType": "assistant-only",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """Based on the fact sheet, we are analyzing the following PE fund:
**Fund Structure:**
- **Type:** '40 Act Registered, Closed-End Non-Diversified Fund with Tender Offers
- **Manager:** Hamilton Lane Advisors, LLC
- **AUM:** $4.67 billion (as of August 31, 2025)
- **Inception:** September 2020 (as Evergreen Private Fund L.P.), converted January 2021
- **Strategy:** Direct co-investments (49%) and secondary transactions (51%) in private equity
- **Portfolio:** 157 investments across 153 general partners
""",
            },
            {
                "type": "markdown",
                "content": """I have extracted returns for the Institutional(I) Shares. 
""",
            },
            {
                "type": "html",
                "content": """<table style="font-size:.8em;">
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
""",
            },
            {
                "type": "markdown",
                "content": """Reported performance is favorable compared to global equities.
""",
            },
            {
                "type": "markdown",
                "content": """However, the monthly returns have been highly smoothed, with extremely low volatility that is not realistic.
""",
            },
            {
                "type": "markdown",
                "content": """As you know, this is a well documented issue with PE fund reporting
- Leads to wildly misleading conclusions if not properly addressed.
- [Desmoothing technique](?drawer=desmooth.html) techniques can be applied to attempt to undo the smoothing effects.
""",
            },
        ],
    },
]
