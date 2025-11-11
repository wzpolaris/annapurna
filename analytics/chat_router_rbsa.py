from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from video_script import get_iteration, slide_count
from backend.app.schemas import ResponseBlock, ResponseCard
from backend.app.upload_block import upload_block_component

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
    'summariser': None,
    'slides_mode': False,
    'current_slide_index': 0
}

# initialize
ROUTER_STATE['model'] = os.environ['OPENAI_MODEL']
ROUTER_STATE['project_root'] = Path(__file__).resolve().parent.parent

from typing import List, Union


def process_message(message: str) -> List[ResponseCard]:

    text = message.lower().strip()

    try:
        if text == 'slides':
            logger.info('chat router: entering slides mode.')
            ROUTER_STATE['slides_mode'] = True
            response = _start_slides_mode(message)
        elif ROUTER_STATE.get('slides_mode'):
            response = _next_slide(message)
        else:
            raise Exception('not in slides mode')



        # elif request_rbsa(text):
        #     logger.info('chat router: full RBSA analysis requested.')
        #     summary = run_rbsa()
        #     response = [_mk_user_assistant_card(message, [_mk_markdown_block(summary)])]
        # else:
        #     logger.info('chat router: follow-up requested.')
        #     summary = smart_get_report(message)
        #     logger.info(summary)
        #     response = [_mk_user_assistant_card(message, [_mk_markdown_block(summary)])]

    except Exception as exc:
        logger.error(f"Error processing message: {exc}")
        response = [_mk_user_assistant_card(message, [_mk_markdown_block(f"I encountered an error processing your request: {str(exc)}")])]

    assistant_history: List[str] = []
    for card in response:
        assistant_history.extend(block.content for block in card.assistant_blocks)

    ROUTER_STATE['conversation_history'].extend([
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': '\n\n'.join(assistant_history)}
    ])

    return response


def _start_slides_mode(user_message: str) -> List[ResponseCard]:
    total = slide_count()
    if total == 0:
        ROUTER_STATE['slides_mode'] = False
        ROUTER_STATE['current_slide_index'] = 0
        return [_mk_user_assistant_card(user_message, [_mk_markdown_block('No scripted slides are available.')])]

    iteration = get_iteration(1)
    if iteration is None:
        ROUTER_STATE['slides_mode'] = False
        ROUTER_STATE['current_slide_index'] = 0
        return [_mk_user_assistant_card(user_message, [_mk_markdown_block('No scripted slides are available.')])]

    if iteration.delay:
        time.sleep(iteration.delay)

    ROUTER_STATE['slides_mode'] = True
    ROUTER_STATE['current_slide_index'] = 1
    return _build_response_cards(iteration)


def _next_slide(user_message: str) -> List[ResponseCard]:
    current_raw = ROUTER_STATE.get('current_slide_index', 0)
    try:
        current_index = int(current_raw)
    except (TypeError, ValueError):
        current_index = 0

    next_index = current_index + 1 if current_index else 1
    iteration = get_iteration(next_index)

    if iteration is None:
        ROUTER_STATE['slides_mode'] = False
        ROUTER_STATE['current_slide_index'] = 0
        return [_mk_assistant_only_card([_mk_markdown_block('Reached the end of the scripted slides.')])]

    if iteration.delay:
        time.sleep(iteration.delay)

    ROUTER_STATE['current_slide_index'] = next_index
    return _build_response_cards(iteration)


def _build_response_cards(iteration) -> List[ResponseCard]:
    cards: List[ResponseCard] = []
    for raw in iteration.cards:
        card_type = raw['cardType']
        user_text = raw.get('userText')
        metadata = raw.get('metadata')
        blocks: List[ResponseBlock] = []
        for raw_block in raw.get('assistantBlocks', []) or []:
            block_type = raw_block.get('type')
            if block_type == 'upload' and not raw_block.get('content'):
                content = upload_block_component()
                raw_block = {**raw_block, 'content': content}
            blocks.append(ResponseBlock(**raw_block))
        cards.append(
            ResponseCard(
                card_type=card_type,
                user_text=user_text,
                assistant_blocks=blocks,
                metadata=metadata,
            )
        )
    return cards


def _mk_markdown_block(content: str) -> ResponseBlock:
    return ResponseBlock(type='markdown', content=content)


def _mk_user_assistant_card(user_text: str, blocks: List[ResponseBlock]) -> ResponseCard:
    return ResponseCard(card_type='user-assistant', user_text=user_text, assistant_blocks=blocks)


def _mk_assistant_only_card(blocks: List[ResponseBlock]) -> ResponseCard:
    return ResponseCard(card_type='assistant-only', assistant_blocks=blocks)


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

    import json
 
    model = str(ROUTER_STATE.get('model') or DEFAULT_MODEL)
    
    client = OpenAI()
    
    # Use a simple system prompt for follow-ups
    system_content = """You are a helpful assistant for answering questions about RBSA analysis results. 
        The user has already run an RBSA analysis. Use the provided results data to answer their 
        questions clearly and concisely. Focus on the specific information they're asking about.
    """
    
    # Build messages with simple system prompt
    messages = [
        {'role': 'system', 'content': system_content}
    ]
    
    # Add the JSON results as context instead of full conversation history
    latest_results = ROUTER_STATE.get('latest_results')
    latest_summary = ROUTER_STATE.get('latest_summary')
    
    if latest_results or latest_summary:
        context_message = "Here are the RBSA analysis results:\n\n"
        
        if latest_summary:
            # Provide just the clean summary JSON, not the original instructions
            context_message += f"**Analysis Summary:**\n```json\n{json.dumps(latest_summary, indent=2)}\n```\n\n"
            
        if latest_results and latest_results != latest_summary:
            context_message += f"**Raw Results:**\n```json\n{json.dumps(latest_results, indent=2)}\n```"
            
        messages.append({'role': 'user', 'content': context_message})
    
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


def ORIG_llm_follow_up(question: str) -> str:
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
