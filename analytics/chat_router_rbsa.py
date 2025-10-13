from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, Mapping, Optional

#from dotenv import load_dotenv

from openai import OpenAI

from .chat_openai_rbsa import DEFAULT_MODEL, rbsa_summarize_results, get_rbsa_results
#from .rbsa.rbsa_pipeline import rbsa_main

import logging
logger = logging.getLogger('analytics.rbsa')

RBSA_TRIGGER_PATTERN = re.compile(r'\b(rbsa|return|returns|analysis|style)\b', re.IGNORECASE)
DETAIL_INDICATORS = ('detail', 'detailed', 'full', 'deeper', 'expand', 'comprehensive')

ADDITIONAL_REPORT_KEYWORDS: Dict[str, tuple[str, ...]] = {
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
    'model': '',
    'project_root': None,
    'summariser': None
}

# initialize
ROUTER_STATE['model'] = os.environ['OPENAI_MODEL']
ROUTER_STATE['project_root'] = Path(__file__).resolve().parent.parent


def process_message(message: str) -> str:

    text = message.lower().strip()

    if request_rbsa(text):
        logger.info('chat router: full RBSA analysis requested.')
        return run_rbsa()

    # check for report requested
    report_requested = request_additional_report(text)
    if report_requested:
        time.sleep(2)
        return _get_report(report_requested, text)

    # pass through to LLM
    return llm_passthrough(message)


def run_rbsa() -> str:
    try:
        logger.info('running RBSA analysis pipeline...')
        results = get_rbsa_results()
        logger.info('RBSA analysis pipeline completed.')
    except Exception as exc:
        return f'RBSA analysis failed: {exc}'

    ROUTER_STATE['latest_results'] = results
    ROUTER_STATE['latest_summary'] = None
    ROUTER_STATE['latest_validation_errors'] = []

    logger.info('generating summary via LLM...')
    import time
    t0 = time.time()
    summary_payload = rbsa_summarize_results(results)
    t1 = time.time()
    logger.info(f'LLM summary generation completed in {t1 - t0:.1f} seconds.')

    if 'error' in summary_payload:
        return f'Summary generation failed: {summary_payload["error"]}'

    response_dict = summary_payload.get('response', summary_payload)
    if not isinstance(response_dict, Mapping):
        return 'Summary response malformed.'

    ROUTER_STATE['latest_summary'] = response_dict
    ROUTER_STATE['latest_validation_errors'] = summary_payload.get('validation_errors', [])  # type: ignore[arg-type]

    final_section = get_nested_report(response_dict, SUMMARY_PATHS['final'])
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


def llm_passthrough(message: str) -> str:
    model = str(ROUTER_STATE.get('model') or DEFAULT_MODEL)
    client = OpenAI()
    completion = client.chat.completions.create(
        model = model,
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant for general queries.'},
            {'role': 'user', 'content': message},
        ],
    )
    return completion.choices[0].message.content or ''


def request_rbsa(text: str) -> bool:
    return bool(RBSA_TRIGGER_PATTERN.search(text))


def request_additional_report(text: str) -> Optional[str]:
    for report, keywords in ADDITIONAL_REPORT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return report
    return None


def _is_detailed_request(text: str) -> bool:
    return any(token in text for token in DETAIL_INDICATORS)


def _get_report(report: str, text: str) -> str:

    target_path = SUMMARY_PATHS.get(report)
    if not target_path:
        return 'Requested report is not recognised.'

    summary = ROUTER_STATE.get('latest_summary', None)
    if not isinstance(summary, Mapping):
        return 'No RBSA summary available. Run an RBSA analysis first.'

    section_dict = get_nested_report(summary, target_path)
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


def get_nested_report(report: Mapping[str, object], path: tuple[str, ...]) -> Optional[Mapping[str, object]]:
    current: object = report
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

