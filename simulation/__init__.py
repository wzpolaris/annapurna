"""Playwright simulation package with iteration loading logic."""

from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Mapping, Optional


FORCE_GLOBAL_DELAY = True  # flip to False to honor per-iteration delays
GLOBAL_ITERATION_DELAY = 0.0
TURN_DELAY_DEFAULT = 1.0  # default delay when not specified in turn


@dataclass(frozen=True)
class ScriptIteration:
    cards: List[Dict[str, Any]]
    delay: Optional[float] = None
    pause_required: bool = False


def _iteration_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r'(\d+)', path.stem)
    index = int(match.group(1)) if match else 1_000_000
    return index, path.stem


def _load_iterations(directory: Path) -> List[ScriptIteration]:
    """Load iterations from a specific directory. No caching."""
    base_path = Path(directory)
    iterations: List[ScriptIteration] = []

    for path in sorted(base_path.glob('iter_*.py'), key=_iteration_sort_key):
        # Always use exec for loading from directories
        module_name = path.stem
        namespace = {}
        exec(path.read_text(), namespace)
        # Create a simple object to hold the namespace
        from types import SimpleNamespace
        module = SimpleNamespace(**namespace)

        turns = _extract_turns(module, module_name)
        iterations.extend(turns)

    return iterations


def _extract_turns(module: object, module_name: str) -> List[ScriptIteration]:
    """
    Extract turns from a module.
    Supports: TURNS or ITERATIONS = [{...}, {...}, ...] (case-insensitive)
    Both keywords use the same flattened structure.
    """
    # Get all module attributes in a case-insensitive manner
    module_attrs = {name.upper(): name for name in dir(module) if not name.startswith('_')}

    # Check for TURNS/ITERATIONS format (case-insensitive)
    if 'TURNS' in module_attrs or 'ITERATIONS' in module_attrs:
        attr_name = module_attrs.get('TURNS') or module_attrs.get('ITERATIONS')
        raw = getattr(module, attr_name)
        if not isinstance(raw, (list, tuple)):
            raise ValueError(f'{attr_name} in "{module_name}" must be a list or tuple.')

        turns = []
        for i, turn_data in enumerate(raw):
            if not isinstance(turn_data, Mapping):
                raise ValueError(f'Turn {i} in "{module_name}" must be a mapping.')
            turns.append(_create_iteration_from_data(dict(turn_data)))

        if not turns:
            raise ValueError(f'{attr_name} in "{module_name}" must contain at least one turn.')
        return turns

    else:
        raise ValueError(f'Module "{module_name}" must define TURNS or ITERATIONS (case-insensitive).')


def _create_iteration_from_data(turn_data: Dict[str, Any]) -> ScriptIteration:
    """
    Create a ScriptIteration from turn data dictionary.
    Uses flattened format: {delay, cardType, userText, assistantBlocks, metadata, pause}
    """
    pause_required = bool(turn_data.get('pause') or turn_data.get('pause_required'))

    # Normalize userText with dedent
    user_text = turn_data.get('userText')
    if isinstance(user_text, str):
        user_text = dedent(user_text).strip()

    # Normalize assistantBlocks with dedent
    blocks = turn_data.get('assistantBlocks', []) or []
    if not isinstance(blocks, (list, tuple)):
        raise ValueError('assistantBlocks must be a list when provided')

    normalized_blocks: List[Dict[str, Any]] = []
    for raw_block in blocks:
        if not isinstance(raw_block, Mapping):
            raise ValueError('each assistant block must be a mapping')
        block = dict(raw_block)
        content = block.get('content')
        if isinstance(content, str):
            block['content'] = dedent(content).strip()
        normalized_blocks.append(block)

    # Create a single-card list from the flattened turn data
    card_data: Dict[str, Any] = {
        'cardType': turn_data.get('cardType', 'user-assistant'),
        'userText': user_text,
        'assistantBlocks': normalized_blocks,
    }
    # Include metadata if present
    if 'metadata' in turn_data:
        card_data['metadata'] = turn_data['metadata']

    cards: List[Dict[str, Any]] = [card_data]

    # Get delay with fallback to default
    raw_delay = _coerce_delay(turn_data.get('delay'))
    if raw_delay is None:
        raw_delay = TURN_DELAY_DEFAULT

    # Apply global delay override if enabled
    if FORCE_GLOBAL_DELAY:
        delay = GLOBAL_ITERATION_DELAY
    else:
        delay = raw_delay

    return ScriptIteration(cards=cards, delay=delay, pause_required=pause_required)


def _coerce_delay(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return None
    return delay if delay >= 0 else None


def all_iterations(directory: Path) -> List[ScriptIteration]:
    """Load all iterations from the specified directory."""
    return _load_iterations(directory)


def get_iteration(index: int, directory: Optional[Path] = None) -> Optional[ScriptIteration]:
    """
    Get a specific iteration by index (1-based).
    If directory is provided, loads from that directory.
    If directory is None, loads from default video_script/ directory.
    """
    if directory is None:
        # Default to video_script/ for web app compatibility
        directory = Path(__file__).resolve().parent.parent / "video_script"

    iterations = _load_iterations(directory)
    if 1 <= index <= len(iterations):
        return iterations[index - 1]
    return None


def iteration_count(directory: Optional[Path] = None) -> int:
    """
    Get the total number of iterations.
    If directory is provided, loads from that directory.
    If directory is None, loads from default video_script/ directory.
    """
    if directory is None:
        # Default to video_script/ for web app compatibility
        directory = Path(__file__).resolve().parent.parent / "video_script"

    iterations = _load_iterations(directory)
    return len(iterations)


def slide_count(directory: Optional[Path] = None) -> int:
    """Alias for iteration_count() for backward compatibility."""
    return iteration_count(directory)
