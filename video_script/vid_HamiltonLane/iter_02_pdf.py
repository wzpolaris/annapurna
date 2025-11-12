from backend.app.upload_block import upload_block_component

# --TURN--

delay = 2.0
pause = True

cardType = "user-assistant"

userText = "I can upload a factsheet PDF."

assistantBlocks_type = "markdown"
assistantBlocks_content = "Ok. Please upload the factsheet PDF, and I will extract the returns."

assistantBlocks_type = "upload"
assistantBlocks_content = upload_block_component()

