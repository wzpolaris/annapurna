

# ###################################################
# # --TURN--
# ###################################################

delay = 1.0
cardType = "assistant-only"

# metadata = {'showUserText': False}
# userText = "null"

assistantBlocks_type = "markdown"

assistantBlocks_content = """

Welcome to the Northfield AI powered Analytics Engine.

How can I help you?

"""


# ###################################################
# # --TURN--
# ###################################################

delay = 1.0
cardType = "user-assistant"
metadata = {'showUserText': True}

# - + - + - + - + - + - + - + - + - + - + - + - + -

userText = """

Hey, can you help me prepare for a meeting?

"""

# - + - + - + - + - + - + - + - + - + - + - + - + -

assistantBlocks_type = "markdown"

assistantBlocks_content = """

Yes, I sure can
"""



###################################################
# --TURN--
###################################################

delay = 1.0
cardType = "user-assistant"
metadata = {'showUserText': True}

# - + - + - + - + - + - + - + - + - + - + - + - + -

userText = """

This is a new turn.

"""

# - + - + - + - + - + - + - + - + - + - + - + - + -

assistantBlocks_type = "markdown"

assistantBlocks_content = """

I can see that

"""

# - + - + - + - + - + - + - + - + - + - + - + - + -

assistantBlocks_type = "markdown"

assistantBlocks_content = """

I can see that, too

"""
