TURNS = [
    {
        "delay": 1.0,
        "cardType": "user-assistant",
        "userText": """
I am the chair of an investment committee. In this afternoon's meeting, we will be considering a Private Equity investment.
The fund being considered is the Hamilton Lane Private Assets Fund.
I am aware that there are differing and strong views among the committe members. I want to lead the group through a methodical discussion.
Can you help me prepare for this meeting?

""",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
Yes, I can review information you have and summarize relevant information about the Hamilton Lane Private Assets Fund.
This will help the committee make an informed decision. Do you have something you can upload?

""",
            },
        ],
    },
    {
        "delay": 1.0,
        "cardType": "user-assistant",
        "userText": """
This is a new turn.

""",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
I can see that 

""",
            },
            {
                "type": "markdown",
                "content": """
I can see that, too

""",
            },
        ],
    },
]
