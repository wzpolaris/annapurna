from backend.app.upload_block import upload_block_component


TURNS = [
    {
        "delay": 2.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "I can upload a factsheet PDF.",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """Ok. Please upload the factsheet PDF, and I will extract the returns.""",
            },
            {
                "type": "upload",
                "content": """upload_block_component()""",
            },
        ],
    },
]
