from __future__ import annotations

import json


def upload_block_component() -> str:
    """Return JSON payload describing upload block defaults."""
    payload = {
        "title": "Upload a file or paste data in the text area below",
        "placeholder": "Paste CSV or text data here"
    }
    return json.dumps(payload)
