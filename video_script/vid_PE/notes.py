
# --TURN--

delay = 5.0
pause = True
cardType = "user-assistant"

userText = "The factsheet 1 has been uploaded."

assistantBlocks_type = "markdown"
assistantBlocks_content = """
I am content
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
I am also 
content
"""

# --TURN--

delay = 3.0
pause = False
cardType = "user-assistant"

userText = "The factsheet 2 has been uploaded."

assistantBlocks_type = "markdown"
assistantBlocks_content = """
good job
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
well done
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
chip chip cheerio
"""




TURNS = [
    {
        "delay": 5.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "The factsheet 1 has been uploaded.",  # Short - keep inline
        "assistantBlocks": [
            {"type": "markdown", "content": """
I am content
"""
            },
            {
                "type": "markdown", "content": """
I am also 
content
"""
            }
        ],
    },
    {
        "delay": 3.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "The factsheet 2 has been uploaded.",  # Short - keep inline
        "assistantBlocks": [
            {
                "type": "markdown", 
                "content": """
good job
"""
            },
            {
                "type": "markdown", 
                "content": """
well done
"""
            },
            {
                "type": "markdown", 
                "content": """
chip chip cheerio
"""
            }
        ],
    }
]