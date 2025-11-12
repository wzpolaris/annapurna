"""
Preprocessor for simplified turn format scripts.

Converts flat, semantic Python files into structured TURNS format.

Usage:
    python simulation/preprocess_script.py <input_file> [output_file]

Example input:
    # --TURN--
    delay = 5.0
    userText = "Hello"
    assistantBlocks_type = "markdown"
    assistantBlocks_content = "Response"

Example output:
    TURNS = [
        {
            "delay": 5.0,
            "userText": "Hello",
            "assistantBlocks": [
                {"type": "markdown", "content": "Response"}
            ]
        }
    ]
"""

import re
from pathlib import Path
from typing import Any, Dict, List


def parse_simple_format(content: str) -> List[Dict[str, Any]]:
    """
    Parse simplified turn format into structured TURNS list.

    Format:
        # --TURN--
        delay = 5.0
        pause = True
        cardType = "user-assistant"
        userText = "message"
        assistantBlocks_type = "markdown"
        assistantBlocks_content = '''content'''

    Args:
        content: The raw content of the simple format file

    Returns:
        List of turn dictionaries ready for TURNS list
    """
    turns = []
    lines = content.split('\n')

    current_turn: Dict[str, Any] = {}
    current_blocks: List[Dict[str, str]] = []
    in_multiline = False
    multiline_buffer = []
    multiline_var = None
    quote_type = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect turn boundary - match any line containing --TURN--
        if stripped.startswith('#') and '--TURN--' in stripped:
            # Save previous turn if exists
            if current_turn:
                if current_blocks:
                    current_turn['assistantBlocks'] = current_blocks
                turns.append(current_turn)
            # Start new turn
            current_turn = {}
            current_blocks = []
            i += 1
            continue

        # Skip empty lines and comments (except --TURN--)
        if not stripped or (stripped.startswith('#') and '--TURN--' not in stripped):
            i += 1
            continue

        # Handle multiline strings
        if in_multiline:
            # Check if this line ends the multiline string
            if quote_type in line:
                # Check for proper closing (not escaped)
                if quote_type == '"""' and '"""' in line:
                    # Found closing """
                    before_close = line.split('"""')[0]
                    multiline_buffer.append(before_close)
                    value = '\n'.join(multiline_buffer)

                    # Assign to appropriate variable
                    if multiline_var == 'assistantBlocks_content':
                        if current_blocks:
                            current_blocks[-1]['content'] = value
                    else:
                        current_turn[multiline_var] = value

                    in_multiline = False
                    multiline_buffer = []
                    multiline_var = None
                    quote_type = None
                elif quote_type == "'''" and "'''" in line:
                    # Found closing '''
                    before_close = line.split("'''")[0]
                    multiline_buffer.append(before_close)
                    value = '\n'.join(multiline_buffer)

                    if multiline_var == 'assistantBlocks_content':
                        if current_blocks:
                            current_blocks[-1]['content'] = value
                    else:
                        current_turn[multiline_var] = value

                    in_multiline = False
                    multiline_buffer = []
                    multiline_var = None
                    quote_type = None
                else:
                    multiline_buffer.append(line)
            else:
                multiline_buffer.append(line)
            i += 1
            continue

        # Parse variable assignment
        if '=' in line:
            var_name, _, value_part = line.partition('=')
            var_name = var_name.strip()
            value_part = value_part.strip()

            # Check for multiline string start
            if value_part.startswith('"""'):
                if value_part.endswith('"""') and len(value_part) > 6:
                    # Single line with """..."""
                    value = value_part[3:-3]
                    if var_name == 'assistantBlocks_content':
                        if current_blocks:
                            current_blocks[-1]['content'] = value
                    else:
                        current_turn[var_name] = value
                else:
                    # Start of multiline
                    in_multiline = True
                    multiline_var = var_name
                    quote_type = '"""'
                    # Get content after opening """
                    after_open = value_part[3:]
                    if after_open:
                        multiline_buffer.append(after_open)
            elif value_part.startswith("'''"):
                if value_part.endswith("'''") and len(value_part) > 6:
                    # Single line with '''...'''
                    value = value_part[3:-3]
                    if var_name == 'assistantBlocks_content':
                        if current_blocks:
                            current_blocks[-1]['content'] = value
                    else:
                        current_turn[var_name] = value
                else:
                    # Start of multiline
                    in_multiline = True
                    multiline_var = var_name
                    quote_type = "'''"
                    after_open = value_part[3:]
                    if after_open:
                        multiline_buffer.append(after_open)
            else:
                # Single line value
                # Try to evaluate as Python literal
                try:
                    value = eval(value_part)
                except:
                    value = value_part

                # Handle special variable names
                if var_name == 'assistantBlocks_type':
                    # Start new block
                    current_blocks.append({'type': value})
                elif var_name == 'assistantBlocks_content':
                    # Add content to last block
                    if current_blocks:
                        current_blocks[-1]['content'] = value
                else:
                    # Regular turn property
                    current_turn[var_name] = value

        i += 1

    # Save final turn
    if current_turn:
        if current_blocks:
            current_turn['assistantBlocks'] = current_blocks
        turns.append(current_turn)

    return turns


def format_turns_output(turns: List[Dict[str, Any]], imports: List[str] = None) -> str:
    """
    Format TURNS list as Python code with proper indentation.

    Args:
        turns: List of turn dictionaries
        imports: Optional list of import statements to include at top

    Returns:
        Formatted Python code string
    """
    lines = []

    # Add imports if provided
    if imports:
        for imp in imports:
            lines.append(imp)
        lines.append("")
        lines.append("")

    lines.append("TURNS = [")

    for turn in turns:
        lines.append("    {")

        # Add turn properties in consistent order
        property_order = ['delay', 'pause', 'cardType', 'metadata', 'userText', 'assistantBlocks']

        for key in property_order:
            if key not in turn:
                continue

            value = turn[key]

            if key == 'assistantBlocks':
                # Handle assistantBlocks specially
                lines.append('        "assistantBlocks": [')
                for block in value:
                    lines.append("            {")
                    lines.append(f'                "type": "{block["type"]}",')

                    content = block['content']
                    if '\n' in content:
                        lines.append('                "content": """')
                        lines.append(content)
                        lines.append('""",')
                    else:
                        lines.append(f'                "content": """{content}""",')

                    lines.append("            },")
                lines.append("        ],")
            elif isinstance(value, str):
                if '\n' in value:
                    lines.append(f'        "{key}": """')
                    lines.append(value)
                    lines.append('""",')
                else:
                    # Escape quotes in the string
                    escaped_value = value.replace('"', '\\"')
                    lines.append(f'        "{key}": "{escaped_value}",')
            elif isinstance(value, bool):
                lines.append(f'        "{key}": {str(value)},')
            elif isinstance(value, (int, float)):
                lines.append(f'        "{key}": {value},')
            elif isinstance(value, dict):
                # For metadata
                lines.append(f'        "{key}": {repr(value)},')
            else:
                lines.append(f'        "{key}": {repr(value)},')

        lines.append("    },")

    lines.append("]")
    return '\n'.join(lines)


def extract_imports(content: str) -> List[str]:
    """
    Extract import statements from the beginning of the file.

    Args:
        content: The raw file content

    Returns:
        List of import statement lines
    """
    imports = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            imports.append(line.rstrip())
        elif stripped and not stripped.startswith('#'):
            # Stop at first non-import, non-comment line
            break
    return imports


def detect_format(file_path: Path) -> str:
    """
    Detect whether a file is in simple or structured format.

    Args:
        file_path: Path to the file to check

    Returns:
        'simple' if file uses # --TURN-- format, 'structured' if it uses TURNS = []
    """
    content = file_path.read_text()

    # Check for simple format marker
    if '# --TURN--' in content:
        return 'simple'

    # Check for structured format
    if 'TURNS = [' in content or 'TURNS=[' in content:
        return 'structured'

    # Case-insensitive check for TURNS/turns/Turns
    import re
    if re.search(r'(?:TURNS|turns|Turns)\s*=\s*\[', content):
        return 'structured'

    # Default to structured if unclear
    return 'structured'


def prepare_video_directory(video_name: str, base_dir: Path = None) -> Path:
    """
    Prepare a video directory for simulation by converting all files to structured format.

    Process:
    1. Find all iter_*.py files in video_script/{video_name}/
    2. Detect format of each file (simple vs structured)
    3. Convert simple → structured, or copy structured as-is
    4. Place results in video_script/{video_name}/_tmp/
    5. Return path to _tmp directory

    Args:
        video_name: Name of the video subdirectory
        base_dir: Base directory (defaults to video_script/)

    Returns:
        Path to the _tmp directory with structured format files
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent / "video_script"

    video_dir = base_dir / video_name
    tmp_dir = video_dir / "_tmp"

    if not video_dir.exists():
        raise ValueError(f"Video directory not found: {video_dir}")

    # Create or clear _tmp directory
    if tmp_dir.exists():
        # Remove all files in _tmp directory
        import shutil
        for item in tmp_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
    else:
        # Create _tmp directory
        tmp_dir.mkdir(parents=True, exist_ok=True)

    # Find all iter_*.py files
    iter_files = sorted(video_dir.glob("iter_*.py"))

    if not iter_files:
        raise ValueError(f"No iter_*.py files found in {video_dir}")

    print(f"Preparing video directory: {video_name}")
    print(f"Found {len(iter_files)} iteration files")
    print()

    converted_count = 0
    copied_count = 0

    for file in iter_files:
        output_path = tmp_dir / file.name
        format_type = detect_format(file)

        if format_type == 'simple':
            # Convert simple to structured
            print(f"  Converting {file.name} (simple → structured)")
            convert_file(file, output_path)
            converted_count += 1
        else:
            # Copy structured as-is
            print(f"  Copying {file.name} (already structured)")
            import shutil
            shutil.copy2(file, output_path)
            copied_count += 1

    print()
    print(f"✓ Prepared {len(iter_files)} files in {tmp_dir}")
    print(f"  Converted: {converted_count}")
    print(f"  Copied: {copied_count}")

    return tmp_dir


def convert_file(input_path: Path, output_path: Path = None) -> None:
    """
    Convert a simple format file to structured format.

    Args:
        input_path: Path to input file in simple format
        output_path: Path to output file (defaults to input_path)
    """
    content = input_path.read_text()

    # Extract any import statements
    imports = extract_imports(content)

    # Parse turns
    turns = parse_simple_format(content)

    if not turns:
        print(f"⚠ No turns found in {input_path.name}")
        return

    # Format output
    output = format_turns_output(turns, imports)

    if output_path is None:
        output_path = input_path

    output_path.write_text(output + '\n')
    print(f"✓ Converted {input_path.name}")
    print(f"  → {len(turns)} turns")
    print(f"  → {output_path}")


def convert_directory(directory: Path, pattern: str = "*_simple.py") -> None:
    """
    Convert all files matching pattern in directory.

    Args:
        directory: Directory to search
        pattern: Glob pattern for files to convert (default: *_simple.py)
    """
    files = list(directory.glob(pattern))

    if not files:
        print(f"No files matching '{pattern}' found in {directory}")
        return

    print(f"Found {len(files)} files to convert:")
    for file in files:
        # Generate output filename by removing _simple suffix
        output_name = file.name.replace('_simple.py', '.py')
        output_path = file.parent / output_name

        convert_file(file, output_path)
        print()


def convert_structured_to_simple(turns: List[Dict[str, Any]], imports: List[str] = None) -> str:
    """
    Convert structured TURNS format back to simple format.

    Args:
        turns: List of turn dictionaries
        imports: Optional list of import statements

    Returns:
        Simple format string
    """
    lines = []

    # Add imports if provided
    if imports:
        for imp in imports:
            lines.append(imp)
        lines.append("")

    for turn in turns:
        lines.append("# --TURN--")
        lines.append("")

        # Add turn properties
        if 'delay' in turn:
            lines.append(f"delay = {turn['delay']}")
        if 'pause' in turn:
            lines.append(f"pause = {turn['pause']}")
        if 'cardType' in turn:
            lines.append(f'cardType = "{turn["cardType"]}"')
        if 'metadata' in turn:
            lines.append(f"metadata = {turn['metadata']}")

        lines.append("")

        if 'userText' in turn:
            user_text = turn['userText']
            if '\n' in user_text:
                lines.append('userText = """')
                lines.append(user_text)
                lines.append('"""')
            else:
                lines.append(f'userText = "{user_text}"')

        lines.append("")

        # Add assistant blocks
        if 'assistantBlocks' in turn:
            for block in turn['assistantBlocks']:
                block_type = block.get('type', 'markdown')
                lines.append(f'assistantBlocks_type = "{block_type}"')

                content = block.get('content', '')
                # Check if content is a function call (like upload_block_component())
                if isinstance(content, str):
                    if '\n' in content:
                        lines.append('assistantBlocks_content = """')
                        lines.append(content)
                        lines.append('"""')
                    else:
                        lines.append(f'assistantBlocks_content = "{content}"')
                else:
                    # For function calls, we need to preserve them as code
                    lines.append(f'assistantBlocks_content = {repr(content)}')

                lines.append("")

    return '\n'.join(lines)


def deconvert_file(input_path: Path, output_path: Path = None) -> None:
    """
    Convert structured format file back to simple format.

    Args:
        input_path: Path to structured format file
        output_path: Path to output file (defaults to input_path with _simple suffix)
    """
    # Read and execute the file to get TURNS
    content = input_path.read_text()

    # Extract imports
    imports = extract_imports(content)

    # Execute the file to get TURNS variable
    namespace = {}
    exec(content, namespace)

    if 'TURNS' not in namespace:
        print(f"⚠ No TURNS found in {input_path.name}")
        return

    turns = namespace['TURNS']

    # Convert to simple format
    output = convert_structured_to_simple(turns, imports)

    if output_path is None:
        # Add _simple suffix before .py
        stem = input_path.stem
        output_path = input_path.parent / f"{stem}_simple.py"

    output_path.write_text(output)
    print(f"✓ Converted {input_path.name} to simple format")
    print(f"  → {len(turns)} turns")
    print(f"  → {output_path}")


def deconvert_directory(input_dir: Path, output_dir: Path, pattern: str = "iter_*.py") -> None:
    """
    Convert all structured format files in directory to simple format.

    Args:
        input_dir: Source directory with structured format files
        output_dir: Destination directory for simple format files
        pattern: Glob pattern for files to convert
    """
    files = [f for f in input_dir.glob(pattern) if not f.name.endswith('_simple.py')]

    if not files:
        print(f"No files matching '{pattern}' found in {input_dir}")
        return

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(files)} files to convert:")
    print()

    for file in files:
        # Keep the same filename in output directory
        output_path = output_dir / file.name

        try:
            deconvert_file(file, output_path)
            print()
        except Exception as e:
            print(f"✗ Error converting {file.name}: {e}")
            print()


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Simple to Structured:")
        print("    python simulation/preprocess_script.py <input_file> [output_file]")
        print("    python simulation/preprocess_script.py --dir <directory> [pattern]")
        print()
        print("  Structured to Simple (reverse):")
        print("    python simulation/preprocess_script.py --reverse <input_file> [output_file]")
        print("    python simulation/preprocess_script.py --reverse-dir <input_dir> <output_dir> [pattern]")
        print()
        print("Examples:")
        print("  # Convert simple to structured")
        print("  python simulation/preprocess_script.py video_script/iter_03_simple.py")
        print()
        print("  # Convert structured to simple (reverse)")
        print("  python simulation/preprocess_script.py --reverse video_script/iter_03_data.py")
        print()
        print("  # Convert all structured files to simple format in new directory")
        print("  python simulation/preprocess_script.py --reverse-dir video_script video_script/vid_HamiltonLane")
        sys.exit(1)

    if sys.argv[1] == '--dir':
        # Directory mode: simple to structured
        directory = Path(sys.argv[2])
        pattern = sys.argv[3] if len(sys.argv) > 3 else "*_simple.py"
        convert_directory(directory, pattern)

    elif sys.argv[1] == '--reverse':
        # Reverse mode: structured to simple
        input_file = Path(sys.argv[2])
        output_file = Path(sys.argv[3]) if len(sys.argv) > 3 else None

        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

        deconvert_file(input_file, output_file)

    elif sys.argv[1] == '--reverse-dir':
        # Reverse directory mode: structured to simple
        if len(sys.argv) < 4:
            print("Error: --reverse-dir requires input and output directories")
            print("Usage: python simulation/preprocess_script.py --reverse-dir <input_dir> <output_dir> [pattern]")
            sys.exit(1)

        input_dir = Path(sys.argv[2])
        output_dir = Path(sys.argv[3])
        pattern = sys.argv[4] if len(sys.argv) > 4 else "iter_*.py"

        deconvert_directory(input_dir, output_dir, pattern)

    else:
        # Single file mode: simple to structured
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

        if not input_file.exists():
            print(f"Error: File not found: {input_file}")
            sys.exit(1)

        convert_file(input_file, output_file)


if __name__ == "__main__":
    main()
