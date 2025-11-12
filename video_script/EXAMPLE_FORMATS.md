# Iteration File Format

This document shows the format for `iter_*.py` files.

## Format Structure

All iteration files must use either `TURNS` or `ITERATIONS` (case-insensitive) with a flattened structure:

```python
TURNS = [
    {
        "delay": 1.0,  # Optional - defaults to TURN_DELAY_DEFAULT (1.0) if omitted
        "pause": False,  # Optional - defaults to False
        "cardType": "user-assistant",
        "userText": "First turn message",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "Response content"
            }
        ],
    },
    {
        "delay": 1.5,
        "cardType": "user-assistant",
        "userText": "Second turn message",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "Second response"
            }
        ],
    },
    {
        # No delay specified - will use TURN_DELAY_DEFAULT (1.0)
        "cardType": "assistant-only",
        "metadata": {"showUserText": False},
        "userText": "backend command",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "Third turn, assistant-only"
            }
        ],
    }
]
```

## Alternative Keyword: ITERATIONS

Both `TURNS` and `ITERATIONS` are supported and use the **exact same structure**:

```python
iterations = [  # Case-insensitive: ITERATIONS, Iterations, etc. all work
    {
        "cardType": "user-assistant",
        "userText": "Message text",
        "assistantBlocks": [...]
    }
]
```

## Turn Structure Fields

Each turn dictionary supports the following fields:

### Required Fields:
- `cardType`: Type of card - usually `"user-assistant"` or `"assistant-only"`
- `userText`: The user's message text
- `assistantBlocks`: List of response blocks from the assistant

### Optional Fields:
- `delay`: Number (float) - delay in seconds before response (defaults to `TURN_DELAY_DEFAULT = 1.0`)
- `pause`: Boolean - whether to pause simulation (defaults to `False`)
- `metadata`: Dict - additional metadata like `{"showUserText": False}`

## Assistant Block Types

Assistant blocks can be of different types:

```python
"assistantBlocks": [
    {
        "type": "markdown",
        "content": "Text response"
    },
    {
        "type": "upload",
        "content": upload_block_component()
    }
]
```

## Key Points

- **Both TURNS and ITERATIONS use identical structure** - they are synonyms
- **Case-Insensitive**: `TURNS`, `turns`, `Turns`, `ITERATIONS`, `iterations`, etc. all work
- **Flattened Structure**: No `cards` wrapper - put card fields directly in the turn dict
- **Optional Delay**: If `delay` is omitted, defaults to `TURN_DELAY_DEFAULT` (1.0 seconds)
- **Multi-Turn Support**: A single `iter_*.py` file can contain multiple turns
- Each turn in the list will be processed sequentially during simulation

## Configuration Values

These constants in `video_script/__init__.py` control delay behavior:

- `TURN_DELAY_DEFAULT = 1.0` - Used when `delay` is not specified in a turn
- `FORCE_GLOBAL_DELAY = True` - When enabled, overrides all delays with `GLOBAL_ITERATION_DELAY`
- `GLOBAL_ITERATION_DELAY = 0.0` - The override value when `FORCE_GLOBAL_DELAY` is enabled

## Example: Single Turn File

```python
TURNS = [
    {
        "delay": 2.0,
        "cardType": "user-assistant",
        "userText": "What is 2+2?",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "2+2 equals 4."
            }
        ],
    }
]
```

## Example: Multi-Turn Conversation

```python
TURNS = [
    {
        "cardType": "user-assistant",
        "userText": "Hello!",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "Hi! How can I help you?"
            }
        ],
    },
    {
        "delay": 1.5,
        "cardType": "user-assistant",
        "userText": "What services do you offer?",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "I offer data analysis, research, and insights."
            }
        ],
    },
    {
        "cardType": "user-assistant",
        "userText": "Great, thank you!",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": "You're welcome!"
            }
        ],
    }
]
```
