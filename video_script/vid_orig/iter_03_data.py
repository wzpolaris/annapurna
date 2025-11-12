TURNS = [
    {
        "delay": 5.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "The factsheet has been uploaded.",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
Based on the fact sheet, here's what we're evaluating:

**Fund Structure:**
- **Type:** '40 Act Registered, Closed-End Non-Diversified Fund with Tender Offers
- **Manager:** Hamilton Lane Advisors, LLC
- **AUM:** $4.67 billion (as of August 31, 2025)
- **Inception:** September 2020 (as Evergreen Private Fund L.P.), converted January 2021
- **Strategy:** Direct co-investments (49%) and secondary transactions (51%) in private equity
- **Portfolio:** 157 investments across 153 general partners

I found and extracted returns for the I Shares. I also see portfolio allocation information.
We can use these to do preliminary analyses. I will start with the performance information okay?
""",
            }
        ],
    }
]
