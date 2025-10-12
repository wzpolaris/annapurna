from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RESULT_KEYS = {
    'results_final',
    'results_desmoothing',
    'results_approach_A',
    'results_approach_B',
    'results_approach_C',
    'results_approach_D',
    'results_substitution',
}

PLACEHOLDER_PATTERN = re.compile(r'\{\{<([^>]+)>\}\}')


def _escape_for_json(value: str) -> str:
    escaped = json.dumps(value)
    return escaped[1:-1]


def _build_placeholder_files(root: Path) -> Dict[str, Path]:
    prompts_dir = root / 'analytics' / 'prompts'
    mapping: Dict[str, Path] = {
        'system_prompt.md': prompts_dir / 'system_prompt.md',
        'overview_desmoothing.md': prompts_dir / 'overview_desmoothing.md',
        'overview_approach_A.md': prompts_dir / 'overview_approach_A.md',
        'overview_approach_B.md': prompts_dir / 'overview_approach_B.md',
        'overview_approach_C.md': prompts_dir / 'overview_approach_C.md',
        'overview_approach_D.md': prompts_dir / 'overview_approach_D.md',
        'overview_substition.md': prompts_dir / 'overview_substitution.md',
        'config.yaml': root / 'config.yaml',
    }
    missing = [name for name, path in mapping.items() if not path.exists()]
    if missing:
        joined = ', '.join(missing)
        raise FileNotFoundError(f'Failed to locate placeholder files: {joined}')
    return mapping


def _default_results_payload() -> Dict[str, Any]:
    return {key: {} for key in RESULT_KEYS}


def render_prompt(
    *,
    project_root: Path | None = None,
    results: Mapping[str, Any] | None = None,
) -> str:
    root = project_root or PROJECT_ROOT
    placeholder_files = _build_placeholder_files(root)
    prompts_dir = root / 'analytics' / 'prompts'

    template_path = prompts_dir / 'draft.md'
    if not template_path.exists():
        raise FileNotFoundError(f'Cannot find draft template at {template_path}')

    template = template_path.read_text(encoding='utf-8')

    result_payload = _default_results_payload()
    if results:
        for key in RESULT_KEYS:
            if key in results:
                result_payload[key] = results[key]  # type: ignore[index]

    def replacement(match: re.Match[str]) -> str:
        key = match.group(1)

        if key in RESULT_KEYS:
            return json.dumps(result_payload[key], indent=2)

        if key not in placeholder_files:
            raise KeyError(f'Unsupported placeholder: {key}')

        content = placeholder_files[key].read_text(encoding='utf-8')
        return _escape_for_json(content)

    return PLACEHOLDER_PATTERN.sub(replacement, template)


def build_messages(
    *,
    project_root: Path | None = None,
    results: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    rendered = render_prompt(project_root=project_root, results=results)
    system_message = (
        'You are a financial analysis assistant. Follow the user instructions carefully '
        'and respond with valid JSON that matches the requested schema.'
    )
    return [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': rendered},
    ]


__all__ = ['render_prompt', 'build_messages']
