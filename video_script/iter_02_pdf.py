from backend.app.upload_block import upload_block_component

ITERATION = {
    "user": "I can upload a factsheet PDF.",
    "assistant_blocks": [
        {
            "type": "markdown",
            "content": "Ok. Please upload the factsheet PDF, and I will extract the returns.",
        },
        {
            "type": "upload",
            "content": upload_block_component(),
        },
    ],
    "delay": 2.0,
    "pause": True,
}