from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import re
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class ScriptIteration:
    cards: List[Dict[str, Any]]
    delay: Optional[float] = None
    pause_required: bool = False


_ITERATIONS: List[ScriptIteration] = []


def _iteration_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r'(\\d+)', path.stem)
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
            raise ValueError(f'ITERATION in \"{module_name}\" must be a mapping.')

    if iteration_data is not None:
        cards = _coerce_cards(iteration_data.get('cards'))
        delay = _coerce_delay(iteration_data.get('delay'))
        pause_required = bool(iteration_data.get('pause') or iteration_data.get('pause_required'))
    else:
        cards = _coerce_cards(getattr(module, 'CARDS', None))
        delay = _coerce_delay(getattr(module, 'DELAY_SECONDS', None))
        pause_required = bool(getattr(module, 'PAUSE_REQUIRED', False))

    return ScriptIteration(cards=cards, delay=delay, pause_required=pause_required)


def _coerce_cards(value: object) -> List[Dict[str, Any]]:
    if value is None:
        raise ValueError('cards must be provided for each scripted iteration.')
    if not isinstance(value, (list, tuple)):
        raise ValueError('cards must be a list of mappings')
    result: List[Dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError('card entries must be mappings')
        card = dict(item)
        card_type = card.get('cardType')
        if not isinstance(card_type, str) or not card_type.strip():
            raise ValueError('each card must define a non-empty cardType')
        user_text = card.get('userText')
        if isinstance(user_text, str):
            card['userText'] = dedent(user_text).strip()
        blocks = card.get('assistantBlocks', []) or []
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
        card['assistantBlocks'] = normalized_blocks
        result.append(card)
    if not result:
        raise ValueError('cards must contain at least one card definition')
    return result


def _coerce_delay(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        delay = float(value)
    except (TypeError, ValueError):
        return None
    return delay if delay >= 0 else None


def get_iteration(index: int) -> Optional[ScriptIteration]:
    _load_iterations()
    if 1 <= index <= len(_ITERATIONS):
        return _ITERATIONS[index - 1]
    return None


def iteration_count() -> int:
    _load_iterations()
    return len(_ITERATIONS)


def slide_count() -> int:
    return iteration_count()


def all_iterations() -> List[ScriptIteration]:
    _load_iterations()
    return list(_ITERATIONS)
