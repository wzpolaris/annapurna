from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, Mapping, Optional

#from dotenv import load_dotenv

from openai import OpenAI

from .chat_openai_rbsa import DEFAULT_MODEL, rbsa_summarize_results, get_rbsa_results
from .chat_template_rbsa import build_system_context
from .llm_request_classifier import classify_rbsa_request
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
    'conversation_history': [],
    'original_system_prompt': None,
    'model': '',
    'project_root': None,
    'summariser': None
}

# initialize
ROUTER_STATE['model'] = os.environ['OPENAI_MODEL']
ROUTER_STATE['project_root'] = Path(__file__).resolve().parent.parent

def process_message(message: str) -> str:

    text = message.lower().strip()
    
    try:
        if request_rbsa(text):
            logger.info('chat router: full RBSA analysis requested.')
            response = run_rbsa()
        else:
            # Use LLM-based classification for intelligent routing
            logger.info('chat router: follow-up requested.')
            response = smart_get_report(message)
            logger.info(response)
                
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        response = f"I encountered an error processing your request: {str(e)}"
    
    # Add to history once, regardless of success/failure
    ROUTER_STATE['conversation_history'].extend([
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': response}
    ])

    return response


def run_rbsa() -> str:
    try:
        logger.info('running RBSA analysis pipeline...')
        results = get_rbsa_results()
        logger.info('RBSA analysis pipeline completed.')
    except Exception as exc:
        return f'RBSA analysis failed: {exc}'

    ROUTER_STATE['latest_results'] = results
    ROUTER_STATE['latest_validation_errors'] = []
    
    # Store the original system prompt used for RBSA analysis
    ROUTER_STATE['original_system_prompt'] = build_system_context(results=results)

    logger.info('generating summary via LLM...')
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


def llm_follow_up(question: str) -> str:
    model = str(ROUTER_STATE.get('model') or DEFAULT_MODEL)
    
    client = OpenAI()
    
    # Use original system prompt if available, otherwise fallback to generic
    original_prompt = ROUTER_STATE.get('original_system_prompt')
    if original_prompt and isinstance(original_prompt, str):
        system_content = original_prompt
    else:
        system_content = 'You are a helpful assistant for answering questions about RBSA analysis results and financial analysis. Use the conversation history to provide contextual responses.'
    
    # Build messages with original system prompt and full conversation history
    messages = [
        {'role': 'system', 'content': system_content}
    ]
    
    # Add conversation history for context
    conversation_history = ROUTER_STATE.get('conversation_history', [])
    recent_history = conversation_history
    messages.extend(recent_history)
    
    # Add the new question
    messages.append({'role': 'user', 'content': question})
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return completion.choices[0].message.content or 'Sorry, I could not generate a response.'
    except Exception as e:
        logger.error(f"LLM follow-up failed: {e}")
        return f"I'm having trouble processing your question. Please try again."


def llm_passthrough(message: str) -> str:
    model = str(ROUTER_STATE.get('model') or DEFAULT_MODEL)
    client = OpenAI()
    
    # Build messages with conversation history
    messages = [
        {'role': 'system', 'content': 'You are a helpful assistant for general queries about financial analysis and RBSA.'}
    ]
    
    # Add conversation history for context (limit to avoid token limits)
    conversation_history = ROUTER_STATE.get('conversation_history', [])
    #recent_history = conversation_history[-10:] if isinstance(conversation_history, list) else []
    recent_history = conversation_history
    messages.extend(recent_history)
    
    # Add current message
    messages.append({'role': 'user', 'content': message})
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return completion.choices[0].message.content or 'Sorry, I could not generate a response.'
    except Exception as e:
        logger.error(f"LLM passthrough failed: {e}")
        return f"I'm having trouble connecting to the AI service. Please try again."


def request_rbsa(text: str) -> bool:
    return bool(RBSA_TRIGGER_PATTERN.search(text))


def smart_get_report(user_message: str) -> str:
    """
    Use LLM to classify user request and return appropriate RBSA report section.
    """
    # Check if we have RBSA summary available
    summary = ROUTER_STATE.get('latest_summary', None)
    if not isinstance(summary, Mapping):
        return 'No RBSA summary available. Run an RBSA analysis first.'
    
    # Use LLM to classify the request
    logger.info(f'chat router: classifying request with LLM: "{user_message}"')
    classification = classify_rbsa_request(user_message)
    
    logger.info(f'chat router: classification result - report: {classification["report_type"]}, '
               f'summary: {classification["summary_type"]}, confidence: {classification["confidence"]:.2f}')
    
    # If confidence is too low, fall back to generic LLM
    if classification['confidence'] < 0.3:
        logger.info('chat router: low confidence classification, falling back to LLM follow-up')
        return llm_follow_up(user_message)
    
    # If unknown report type, fall back to generic LLM  
    if classification['report_type'] == 'unknown':
        logger.info('chat router: unknown report type, falling back to LLM follow-up')
        return llm_follow_up(user_message)
        
    # Get the appropriate section path
    report_type = classification['report_type']
    target_path = SUMMARY_PATHS.get(report_type)
    if not target_path:
        logger.warning(f'chat router: no path found for report type: {report_type}')
        return llm_follow_up(user_message)
    
    # Get the section data
    section_dict = get_nested_report(summary, target_path)
    if not section_dict:
        return f'The {report_type} section is not available in the latest RBSA summary.'
    
    # Determine which summary type to return
    summary_type = classification['summary_type']
    if summary_type == 'detailed':
        field_name = 'Detailed Summary'
    elif summary_type == 'executive':
        field_name = 'Executive Summary'
    else:  # 'either' - default to detailed if available, executive otherwise
        if section_dict.get('Detailed Summary'):
            field_name = 'Detailed Summary'
        else:
            field_name = 'Executive Summary'
    
    # Extract the summary text
    summary_text = section_dict.get(field_name) if isinstance(section_dict, Mapping) else None
    
    if isinstance(summary_text, str):
        logger.info(f'chat router: returning {field_name.lower()} for {report_type}')
        return summary_text
    
    # Fallback to alternative summary type
    alternative_field = 'Executive Summary' if field_name == 'Detailed Summary' else 'Detailed Summary'
    alternative = section_dict.get(alternative_field) if isinstance(section_dict, Mapping) else None
    if isinstance(alternative, str):
        logger.info(f'chat router: falling back to {alternative_field.lower()} for {report_type}')
        return alternative
    
    return f'The requested {field_name.lower()} for {report_type} is not available.'


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




