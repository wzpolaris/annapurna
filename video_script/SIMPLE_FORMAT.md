# Simple Turn Format

This document describes the simplified format for authoring turn scripts with minimal boilerplate.

## Why Use Simple Format?

The simple format lets you write content with **zero indentation** and minimal structure:

**Simple Format** (what you write):
```python
# --TURN--

delay = 5.0
pause = True
cardType = "user-assistant"

userText = "The factsheet has been uploaded."

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Based on the fact sheet, here's what we're evaluating:

**Fund Structure:**
- **Type:** '40 Act Registered
- **Manager:** Hamilton Lane Advisors, LLC
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
I will now analyze the performance data.
"""
```

**Gets converted to** (structured format):
```python
TURNS = [
    {
        "delay": 5.0,
        "pause": True,
        "cardType": "user-assistant",
        "userText": "The factsheet has been uploaded.",
        "assistantBlocks": [
            {
                "type": "markdown",
                "content": """
Based on the fact sheet, here's what we're evaluating:

**Fund Structure:**
- **Type:** '40 Act Registered
- **Manager:** Hamilton Lane Advisors, LLC
"""
            },
            {
                "type": "markdown",
                "content": """
I will now analyze the performance data.
"""
            }
        ],
    }
]
```

## Format Specification

### Turn Boundary

Each turn starts with a comment marker:
```python
# --TURN--
```

### Turn Properties

Simple variable assignments:
```python
delay = 5.0          # Optional - defaults to TURN_DELAY_DEFAULT (1.0)
pause = True         # Optional - defaults to False
cardType = "user-assistant"  # Optional - defaults to "user-assistant"
userText = "User's message"
```

### Assistant Blocks

Multiple assistant blocks are defined by repeating the type/content pattern:

```python
assistantBlocks_type = "markdown"
assistantBlocks_content = """
First response block
"""

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Second response block
"""

assistantBlocks_type = "upload"
assistantBlocks_content = upload_block_component()
```

Each pair of `assistantBlocks_type` and `assistantBlocks_content` creates one block.

### Multiline Strings

Use triple quotes for multiline content:
```python
assistantBlocks_content = """
This is paragraph one.

This is paragraph two with a blank line above.
"""
```

Single or double quotes work:
```python
assistantBlocks_content = '''
Alternative multiline syntax
'''
```

## Converting Files

Use the preprocessor script in the `simulation` directory to transform simple format to structured format:

```bash
# Convert in place (overwrites file)
python simulation/preprocess_script.py video_script/iter_03_simple.py

# Convert to different file
python simulation/preprocess_script.py video_script/iter_03_simple.py video_script/iter_03_data.py

# Convert all *_simple.py files in a directory
python simulation/preprocess_script.py --dir video_script

# Convert with custom pattern
python simulation/preprocess_script.py --dir video_script 'iter_*_draft.py'
```

## Workflow

1. **Author** content in simple format for easy editing
2. **Convert** to structured format using the parser
3. **Run** simulation with structured format files

## Example: Complete File

```python
# video_script/iter_example_simple.py

# --TURN--

delay = 2.0
cardType = "user-assistant"
userText = "Hello!"

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Hi! How can I help you today?
"""

# --TURN--

delay = 1.5
cardType = "user-assistant"
userText = "I need help with data analysis."

assistantBlocks_type = "markdown"
assistantBlocks_content = """
I'd be happy to help with data analysis.

What type of data are you working with?
"""

# --TURN--

cardType = "user-assistant"
userText = "Financial data for private equity funds."

assistantBlocks_type = "markdown"
assistantBlocks_content = """
Great! I can help analyze private equity fund data.

Please upload your data file and I'll get started.
"""

assistantBlocks_type = "upload"
assistantBlocks_content = upload_block_component()
```

## Tips

1. **Zero Indentation**: Write all content at the left margin - no indentation needed!
2. **Optional Fields**: Omit `delay`, `pause`, or `cardType` to use defaults
3. **Multiple Blocks**: Just repeat `assistantBlocks_type` / `assistantBlocks_content` pairs
4. **Comments**: Use `#` for comments (except for `# --TURN--` marker)
5. **Formatting**: Markdown formatting works normally in content blocks

## Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `delay` | float | No | 1.0 | Delay in seconds before response |
| `pause` | bool | No | False | Whether to pause simulation |
| `cardType` | string | No | "user-assistant" | Type of card ("user-assistant" or "assistant-only") |
| `userText` | string | Yes | - | The user's message text |
| `assistantBlocks_type` | string | Yes | - | Block type ("markdown", "upload", etc.) |
| `assistantBlocks_content` | string/object | Yes | - | Block content |

## Comparison

### Simple Format Benefits:
- ✅ Zero indentation for content
- ✅ Easy to read and edit
- ✅ Minimal boilerplate
- ✅ Clear structure

### Structured Format Benefits:
- ✅ Valid Python that loads directly
- ✅ IDE support with syntax checking
- ✅ Can be used immediately without conversion

**Best Practice**: Author in simple format, convert to structured format for use.
