from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Dict, Mapping, Optional

from .chat_openai_rbsa import DEFAULT_MODEL, summarize_results
from .rbsa.rbsa_pipeline import rbsa_main

from openai import OpenAI

RBSA_TRIGGER_PATTERN = re.compile(r'\b(rbsa|return|returns|analysis|style)\b', re.IGNORECASE)
DETAIL_INDICATORS = ('detail', 'detailed', 'full', 'deeper', 'expand', 'comprehensive')

SECTION_KEYWORDS: Dict[str, tuple[str, ...]] = {
    'final': ('final', 'overall', 'headline', 'summary', 'wrap', 'conclusion'),
    'desmoothing': ('desmooth', 'smoothing', 'geltn', 'autocorrelation', 'ar(1)'),
    'approach_a': ('approach a', 'nnls', 'stepwise'),
    'approach_b': ('approach b', 'elastic', 'lasso'),
    'approach_c': ('approach c', 'bayes', 'bayesian', 'pip', 'posterior'),
    'approach_d': ('approach d', 'cluster', 'clustering', 'medoid'),
    'substitution': ('substitution', 'substitute', 'replacement', 'swap'),
}

SUMMARY_PATHS: Dict[str, tuple[str, ...]] = {
    'final': ('response', 'Final'),
    'desmoothing': ('response', 'Process', 'De-Smoothing'),
    'approach_a': ('response', 'Process', 'Approach-A'),
    'approach_b': ('response', 'Process', 'Approach-B'),
    'approach_c': ('response', 'Process', 'Approach-C'),
    'approach_d': ('response', 'Process', 'Approach-D'),
    'substitution': ('response', 'Process', 'Substitution'),
}

ROUTER_STATE: Dict[str, object] = {
    'latest_results': None,
    'latest_summary': None,
    'latest_validation_errors': [],
}


def process_message(message: str) -> str:

    text = message.lower().strip()

    # check if rbsa requested
    if _request_rbsa(text):
        return _run_rbsa()

    # check for report requested
    report_requested = _request_additional_report(text)
    if report_requested:
        return _get_report(report_requested)

    # pass through to LLM
    return _llm_passthrough(message)


def _run_rbsa() -> str:

    try:
        results = rbsa_main()
    except Exception as exc:
        return f'RBSA analysis failed: {exc}'

    ROUTER_STATE['latest_results'] = results
    ROUTER_STATE['latest_summary'] = None
    ROUTER_STATE['latest_validation_errors'] = []

    summariser = ROUTER_STATE.get('summariser')
    summary_payload = (
        summariser(results)  # type: ignore[operator]
        if callable(summariser)
        else summarize_results(
            results,
            model=ROUTER_STATE.get('model', DEFAULT_MODEL),  # type: ignore[arg-type]
            project_root=_ensure_path(ROUTER_STATE.get('project_root')),
        )
    )

    if 'error' in summary_payload:
        return f'Summary generation failed: {summary_payload["error"]}'

    response_dict = summary_payload.get('response', summary_payload)
    if not isinstance(response_dict, Mapping):
        return 'Summary response malformed.'

    ROUTER_STATE['latest_summary'] = response_dict
    ROUTER_STATE['latest_validation_errors'] = summary_payload.get('validation_errors', [])  # type: ignore[arg-type]

    final_section = _get_nested(response_dict, SUMMARY_PATHS['final'])
    if not final_section:
        return 'RBSA completed but final summary is unavailable.'

    exec_summary = final_section.get('Executive Summary') if isinstance(final_section, Mapping) else None
    if not isinstance(exec_summary, str):
        return 'RBSA completed but executive summary text is missing.'

    validation_errors = ROUTER_STATE.get('latest_validation_errors', [])
    if validation_errors:
        issues = '\n'.join(f'- {err}' for err in validation_errors)  # type: ignore[arg-type]
        return f'Warnings:\n{issues}\n\n{exec_summary}'

    return exec_summary


def _llm_passthrough(message: str) -> str:
    model = str(ROUTER_STATE.get('model', None))
    if not model:
        raise Exception("Model not configured in router state.")
    client = OpenAI()
    completion = client.chat.completions.create(
        model = model,
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant for general queries.'},
            {'role': 'user', 'content': message},
        ],
    )
    return completion.choices[0].message.content or ''


def _request_rbsa(text: str) -> bool:
    return bool(RBSA_TRIGGER_PATTERN.search(text))


def _request_additional_report(text: str) -> Optional[str]:
    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return section
    return None


def _is_detailed_request(text: str) -> bool:
    return any(token in text for token in DETAIL_INDICATORS)



def _get_report(section: str) -> str:

    target_path = SUMMARY_PATHS.get(section)
    if not target_path:
        return 'Requested section is not recognised.'

    ROUTER_STATE.get('latest_summary')

    section_dict = _get_nested(summary, target_path)
    if not section_dict:
        return 'Requested section is unavailable in the latest RBSA summary.'

    want_detail = _is_detailed_request(text)
    field_name = 'Detailed Summary' if want_detail else 'Executive Summary'
    summary_text = section_dict.get(field_name) if isinstance(section_dict, Mapping) else None

    if isinstance(summary_text, str):
        return summary_text

    alternative = section_dict.get('Detailed Summary') if isinstance(section_dict, Mapping) else None
    if isinstance(alternative, str):
        return alternative

    return 'Requested summary text is unavailable.'


def _get_nested(data: Mapping[str, object], path: tuple[str, ...]) -> Optional[Mapping[str, object]]:
    current: object = data
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return None
        current = current[key]
    return current if isinstance(current, Mapping) else None


def _ensure_path(value: object) -> Optional[Path]:
    if isinstance(value, Path):
        return value
    if isinstance(value, str):
        return Path(value)
    return None


__all__ = ['ROUTER_STATE', 'process_message']
