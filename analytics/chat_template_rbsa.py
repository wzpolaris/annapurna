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

PLACEHOLDER_PATTERN = re.compile(r'\{\{\s*(?:<)?([^>}]+?)(?:>)?\s*\}\}')


def build_llm_messages(
    results: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    system_context = build_system_context(results=results)
    user_context = build_user_context(results=results)
    return [
        {'role': 'system', 'content': system_context},
        {'role': 'user', 'content': user_context},
    ]


# ----------------------------------------------------------------
# --  build sysatem message --
# ----------------------------------------------------------------

def build_system_context(
    results: Mapping[str, Any] | None = None,
) -> str:
    root = PROJECT_ROOT
    placeholder_files = helper_build_placeholder_files()
    prompts_dir = root / 'analytics' / 'prompts'
    template_path = prompts_dir / 'llm_instructions.md'
    if not template_path.exists():
        raise FileNotFoundError(f'Cannot find instructions at {template_path}')

    template = template_path.read_text(encoding='utf-8')
    result_payload = results or {}
    # result_payload = _default_results_payload()
    # if results:
    #     for key in RESULT_KEYS:
    #         if key in results:
    #             result_payload[key] = results[key]  # type: ignore[index]

    return render_system_template(template, placeholder_files=placeholder_files, results=result_payload)


def render_system_template(
    template: str,
    *,
    placeholder_files: Mapping[str, Path],
    results: Mapping[str, Any],
) -> str:
    def replacement(match: re.Match[str]) -> str:
        key = match.group(1)

        if key.startswith('overview_'):
            return _escape_for_json('Overview materials are supplied in the user message payload.')

        if results and key in results:
            return json.dumps(results[key], indent=2)

        if key == 'llm_instructions.md':
            return _escape_for_json('Provided via system role (see instructions above).')

        if key not in placeholder_files:
            return match.group(0)

        print(f"system message build: replacing placeholder: {key}")
        content = placeholder_files[key].read_text(encoding='utf-8')

        return _escape_for_json(content)

    return PLACEHOLDER_PATTERN.sub(replacement, template)


# ----------------------------------------------------------------
# --  build user payload --
# ----------------------------------------------------------------

def build_user_context(
    results: Mapping[str, Any] | None = None,
) -> str:
    
    placeholder_files = helper_build_placeholder_files()
    result_payload = _default_results_payload()

    if results:
        for key in RESULT_KEYS:
            if key in results:
                result_payload[key] = results[key]  # type: ignore[index]

    additional_context = {
        'overview_desmoothing': placeholder_files['overview_desmoothing.md'].read_text(encoding='utf-8'),
        'overview_approach_A': placeholder_files['overview_approach_A.md'].read_text(encoding='utf-8'),
        'overview_approach_B': placeholder_files['overview_approach_B.md'].read_text(encoding='utf-8'),
        'overview_approach_C': placeholder_files['overview_approach_C.md'].read_text(encoding='utf-8'),
        'overview_approach_D': placeholder_files['overview_approach_D.md'].read_text(encoding='utf-8'),
        'overview_substitution': placeholder_files['overview_substition.md'].read_text(encoding='utf-8'),
    }

    analysis_results: dict[str, object] = {
        'results_final': result_payload['results_final'],
        'results_process': {
            'results_desmoothing': result_payload['results_desmoothing'],
            'results_approach_A': result_payload['results_approach_A'],
            'results_approach_B': result_payload['results_approach_B'],
            'results_approach_C': result_payload['results_approach_C'],
            'results_approach_D': result_payload['results_approach_D'],
            'results_substitution': result_payload['results_substitution'],
        },
    }

    payload: dict[str, object] = {
        'system_prompt': placeholder_files['system_prompt.md'].read_text(encoding='utf-8'),
        'additional_context': additional_context,
        'config.yaml': placeholder_files['config.yaml'].read_text(encoding='utf-8'),
        'analysis_results': analysis_results,
    }

    return json.dumps(payload, indent=2)

# ----------------------------------------------------------------
# --  helpers  --
# ----------------------------------------------------------------

def helper_build_placeholder_files() -> Dict[str, Path]:
    prompts_dir = PROJECT_ROOT / 'analytics' / 'prompts'
    mapping: Dict[str, Path] = {
        'system_prompt.md': prompts_dir / 'system_prompt.md',
        'llm_instructions.md': prompts_dir / 'llm_instructions.md',
        'config.yaml': PROJECT_ROOT / 'config.yaml',
        'overview_desmoothing.md': prompts_dir / 'overview_desmoothing.md',
        'overview_approach_A.md': prompts_dir / 'overview_approach_A.md',
        'overview_approach_B.md': prompts_dir / 'overview_approach_B.md',
        'overview_approach_C.md': prompts_dir / 'overview_approach_C.md',
        'overview_approach_D.md': prompts_dir / 'overview_approach_D.md',
        'overview_substition.md': prompts_dir / 'overview_substitution.md',
    }
    missing = [name for name, path in mapping.items() if not path.exists()]
    if missing:
        joined = ', '.join(missing)
        raise FileNotFoundError(f'Failed to locate placeholder files: {joined}')
    return mapping


def _default_results_payload() -> Dict[str, Any]:
    return {key: {} for key in RESULT_KEYS}


def _escape_for_json(value: str) -> str:
    escaped = json.dumps(value)
    return escaped[1:-1]


# def render_prompt(
#     *,
#     project_root: Path | None = None,
#     results: Mapping[str, Any] | None = None,
# ) -> str:
#     return render_user_payload(project_root=project_root, results=results)


#__all__ = ['render_system_message', 'render_user_payload', 'render_prompt', 'build_messages', 'RESULT_KEYS']

if __name__ == '__main__':

    from pprint import pprint

    sample = _default_results_payload()
    sample['results_final'] = {'sample_key': 'sample_value'}
    msg = build_system_context(results=sample)
    # print('--- System Message ---')
    # print(msg)
    # print('--- User Payload ---')
    user = build_user_context(results=sample)
    # print(user)
    msg = build_llm_messages(results=sample)
    pprint(msg)
    print(len(json.dumps(msg)))