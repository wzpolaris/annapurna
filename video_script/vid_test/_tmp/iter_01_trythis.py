TURNS = [
    {
        "delay": 1.0,
        "cardType": "assistant-only",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
Welcome to the Northfield AI powered Analytics Engine.
How can I help you?

""",
            },
        ],
    },
    {
        "delay": 1.0,
        "cardType": "user-assistant",
        "metadata": {'showUserText': True},
        "userText": """
Hey, can you help me prepare for a meeting?

""",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
Yes, I sure can

""",
            },
        ],
    },
    {
        "delay": 1.0,
        "cardType": "user-assistant",
        "metadata": {'showUserText': True},
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
