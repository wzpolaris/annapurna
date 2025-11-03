from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import re
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional
from textwrap import dedent


@dataclass(frozen=True)
class ScriptIteration:
    user: str
    assistant: str
    delay: Optional[float] = None
    pause_required: bool = False
    assistant_blocks: Optional[List[Dict[str, Any]]] = None
    pause_required: bool = False


_ITERATIONS: List[ScriptIteration] = []


def _iteration_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r'(\d+)', path.stem)
    index = int(match.group(1)) if match else 1_000_000
    return index, path.stem


def _load_iterations() -> None:
    if _ITERATIONS:
        return

    base_path = Path(__file__).resolve().parent
    for path in sorted(base_path.glob('iter_*.py'), key=_iteration_sort_key):
        module_name = f'{__name__}.{path.stem}'
        module = import_module(module_name)
        _ITERATIONS.append(_extract_iteration(module, module_name))


def _extract_iteration(module: object, module_name: str) -> ScriptIteration:
    iteration_data: Mapping[str, object] | None = None
    if hasattr(module, 'ITERATION'):
        raw = getattr(module, 'ITERATION')
        if isinstance(raw, Mapping):
            iteration_data = raw
        else:
            raise ValueError(f'ITERATION in "{module_name}" must be a mapping.')

    pause_required = False
    assistant_blocks: Optional[List[Dict[str, Any]]] = None
    if iteration_data is not None:
        user = dedent(str(iteration_data.get('user', '') or '')).strip()
        assistant = dedent(str(iteration_data.get('assistant', '') or '')).strip()
        delay = _coerce_delay(iteration_data.get('delay'))
        pause_required = bool(iteration_data.get('pause') or iteration_data.get('pause_required'))
        assistant_blocks = _coerce_blocks(iteration_data.get('assistant_blocks'))
    else:
        user = dedent(str(getattr(module, 'USER_INPUT', '') or '')).strip()
        assistant = dedent(str(
            getattr(
                module,
                'ASSISTANT_RESPONSE',
                getattr(module, 'SLIDE_RESPONSE', '')
            ) or ''
        )).strip()
        delay = _coerce_delay(getattr(module, 'DELAY_SECONDS', None))
        pause_required = bool(getattr(module, 'PAUSE_REQUIRED', False))
        assistant_blocks = _coerce_blocks(getattr(module, 'ASSISTANT_BLOCKS', None))

    if not assistant and not assistant_blocks:
        raise ValueError(f'Script module "{module_name}" must define assistant content.')

    return ScriptIteration(
        user=user,
        assistant=assistant,
        delay=delay,
        pause_required=pause_required,
        assistant_blocks=assistant_blocks
    )


def _coerce_delay(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return None
    return delay if delay >= 0 else None


def _coerce_blocks(value: object) -> Optional[List[Dict[str, Any]]]:
    if value is None:
        return None
    if isinstance(value, Mapping):
        value = [value]
    if not isinstance(value, (list, tuple)):
        raise ValueError('assistant_blocks must be a list of mappings')
    blocks: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError('assistant block entries must be mappings')
        block: Dict[str, Any] = dict(item)
        content = block.get('content')
        if isinstance(content, str):
            block['content'] = dedent(content).strip()
        blocks.append(block)
    return blocks if blocks else None


def get_iteration(index: int) -> Optional[ScriptIteration]:
    _load_iterations()
    if 1 <= index <= len(_ITERATIONS):
        return _ITERATIONS[index - 1]
    return None


def iteration_count() -> int:
    _load_iterations()
    return len(_ITERATIONS)


def get_slide(index: int) -> Optional[str]:
    iteration = get_iteration(index)
    return iteration.assistant if iteration else None


def slide_count() -> int:
    return iteration_count()


def all_iterations() -> List[ScriptIteration]:
    _load_iterations()
    return list(_ITERATIONS)
