TURNS = [
    {
        "delay": 2.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "How do you address the smoothing issue?",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """**General information on [smoothing](?drawer=desmooth) and [appraisal bias](?drawer=appraisal_bias)...**
An issue with reported private equity returns is that they are appraisal-based, not transaction-based, and this results in artificially smooth time series. The smoothing then leads to several well-documented issues:
- Understatement of estimated volatility and true economic risk
- Lower estimated correlations of PE with public markets
- Masking of tail and liquidity risks, especially during crises
Technically speaking, smoothing is the result of [serial correlation](?drawer=serial_correlation) in the reported returns. So, a [de-smoothing](?drawer=desmooth) analytical adjustment is often applied to get a better estimate of the true risk and return characteristics of PE investments.
Often a de-smoothing adjustment is applied on the Fund's reported returns if the time series is to be used in standard performance and risk analyses including scenario testing, optimization, etc.
I will apply the technique to the Hamilton Lane fund's returns.
---
**Note:** Click on any dotted-underlined term above to learn more!
""",
            },
        ],
    },
]
