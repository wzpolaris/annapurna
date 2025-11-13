TURNS = [
    {
        "delay": 1.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "no, move ahead",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """**Key takeaway from analysis of returns**  
The reported returns for the Hamilton Lane fund are not useful for any meaningful analysis.  
The published returns cannot represent true economic performance. The return series is so heavily smoothed, that even after applying de-smoothing techniques, there is almost no volatility, and the monthly returns are nearly constant.  
With near constant returns, and so little volatility, de-smoothing to amplify the underlying volatility did almost nothing. 
Technically, speaking the AR(1) term was very close to zero (actually -.04 and with no statistical significance).  
**How to proceed?**  
-  Starting with a structural model of private equity as an asset class is preferred.
-  Then, where possible, build up further based upon any other fund-specific information available (Buyout vs VC, vintage, etc.).
""",
            },
        ],
    },
    {
        "delay": 1.0,
        "pause": True,
        "cardType": "assistant-only",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """$y = f(X) + \epsilon$
""",
            },
        ],
    },
    {
        "delay": 1.0,
        "pause": True,
        "cardType": "assistant-only",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """$r_{PE}_{t} = 1.15 r_{GCP}_{t} + 0.25 r_{HY}_{t} + \epsilon_{t}$
""",
            },
        ],
    },
]
