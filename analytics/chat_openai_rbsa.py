from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, cast
import pickle
import time

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from .chat_template_rbsa import RESULT_KEYS, build_llm_messages
from .rbsa.rbsa_pipeline import rbsa_run_pipeline

import logging
logger = logging.getLogger('analytics.rbsa')

from .cache.cacheWithLogging import CacheWithLogging as Cache
timeout_seconds = 60 * 60 * 24 * 14 # 60 seconds * 60 minutes * 24 hours * 14 days
cache_path = Path(__file__).parent.parent / '_cache_diskcache' / 'rbsa_llm_summaries'
if not os.path.isdir(cache_path):
    raise Exception(f'Cache directory does not exist: {cache_path}')
CACHE_SUMMARY_REPORTS = Cache(
    directory=str(cache_path)
    , timeout=timeout_seconds
    , logger=logger
)

SHORT_CIRCUIT = False
SHORT_CIRCUIT_TIME = 2 # 5 seconds

USE_MOCK_DATA = True

DEFAULT_MODEL = os.environ.get('OPENAI_MODEL')


def short_circuit_read():
    try:
        if not SHORT_CIRCUIT:
            return None
        cache_path = Path(__file__).parent.parent / '_cache_diskcache' / 'short_circuit'
        time.sleep(SHORT_CIRCUIT_TIME)
        with open(cache_path / 'short_circuit.pkl', 'rb') as f:
            response_payload = pickle.load(f)
    except:
        response_payload = None
    if response_payload is not None:
        logger.info('Using short-circuited response payload.')
    return response_payload

        
def short_circuit_write(obj: Any):
    try:
        if not SHORT_CIRCUIT:
            return None
        cache_path = Path(__file__).parent.parent / '_cache_diskcache' / 'short_circuit'
        with open(cache_path / 'short_circuit.pkl', 'wb') as f:
            pickle.dump(obj, f)
        logger.info('Writing response payload for short-circuit.')
        return None
    except:
        return None


# def run_llm(model: str, project_root: Path | None = None) -> Mapping[str, Any]:

#     if USE_MOCK_DATA:
#         logger.info('Using mock RBSA results payload.')
#         results_payload = get_mock_results()
#     else:
#         logger.info('Loading RBSA results payload from pipeline.')
#         results_payload = get_rbsa_results()

#     logger.info('Calling LLM to summarize RBSA results...')
#     summary = rbsa_summarize_results(results_payload)
#     if 'response' in summary:
#         # Convert to dict to allow modification
#         result_dict = dict(summary)
#         result_dict['results_payload'] = results_payload
#         return result_dict
#     return summary


def get_exception_results() -> Mapping[str, Any]:
    return {
        'results_final': {},
        'results_desmoothing': {},
        'results_approach_A': {},
        'results_approach_B': {},
        'results_approach_C': {},
        'results_approach_D': {},
        'results_substitution': {},
    }


def get_rbsa_results() -> Mapping[str, Any]:

    logger.info('At beginning of get_rbsa_results()')

    try:
        
        pipeline_output = rbsa_run_pipeline()
        
        analysis_results = pipeline_output.get('analysis_results', {})
        process_results = pipeline_output.get('pipeline_process', {})

        flattened = {
            'results_final': analysis_results.get('results_final', {}),
            'results_desmoothing': process_results.get('results_desmoothing', {}),
            'results_approach_A': process_results.get('results_approach_A', {}),
            'results_approach_B': process_results.get('results_approach_B', {}),
            'results_approach_C': process_results.get('results_approach_C', {}),
            'results_approach_D': process_results.get('results_approach_D', {}),
            'results_substitution': process_results.get('results_substitution', {}),
        }
        print('Loaded RBSA pipeline results.')
        return flattened
    
    except Exception as exc:
        logger.error(f'rbsa_main execution failed: {exc}')
        raise Exception(exc)    


# - Short-circuit and memoize
# -- memoize_with_logging  --

def rbsa_summarize_results(results_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if SHORT_CIRCUIT:
        response_payload = short_circuit_read()
        if response_payload is not None:
            return {'response': response_payload}
    
    return rbsa_summarize_results_cached(results_payload)


CACHE_SUMMARY_REPORTS.memoize(tag='rbsa_summarize_results', typed=True)
def rbsa_summarize_results_cached(
    results_payload: Mapping[str, Any]
) -> Mapping[str, Any]:
    model = str(DEFAULT_MODEL)

    messages = build_llm_messages(results=results_payload)

    response_payload = call_openai(messages, model=model)

    with open(os.path.abspath(os.path.join('./_trap_response','response.json')), 'wb') as f:
        f.write(json.dumps(response_payload, indent=2).encode('utf-8'))
        logger.info('llm response saved to _trap_response/response.json')

    # # BUILT in SHORT_CIRCUIT handling
    # try:
    #     # TODO: remove short circuit eventually
    #     response_payload = None
    #     if SHORT_CIRCUIT:
    #         response_payload = short_circuit_read()
    #     # if short circuit failed or no short circuit
    #     if response_payload is None:
    #         response_payload = call_openai(messages, model=model)
    #     if SHORT_CIRCUIT and response_payload is not None:
    #         short_circuit_write(response_payload)
    # except Exception as exc:  # pragma: no cover - network failure
    #     return {'error': f'OpenAI request failed: {exc}'}

    validation_errors = validate_response(results_payload, response_payload)
    if validation_errors:
        return {
            'validation_errors': validation_errors,
            'response': response_payload
        }
    return {'response': response_payload}


def call_openai(
    messages: Sequence[Mapping[str, str]],
    *,
    model: str,
) -> Mapping[str, Any]:
    client = OpenAI()

    def parse_json(text: str) -> dict[str, Any]:
        return json.loads(text)

    # Convert messages to the correct format for OpenAI
    raw_messages = [
        {'role': message['role'], 'content': message['content']}
        for message in messages
    ]
    chat_messages = cast(Sequence[ChatCompletionMessageParam], raw_messages)

    chat_response = client.chat.completions.create(
        model=model,
        messages=chat_messages,
    )
    content = chat_response.choices[0].message.content or '{}'
    return parse_json(content)


def validate_response(
    results_payload: Mapping[str, Any],
    response_payload: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    expected_flags = _results_has_data_map(results_payload)

    response_root = response_payload.get('response')
    if not isinstance(response_root, dict):
        errors.append('Response missing top-level "response" object.')
        return errors

    data_flags = response_root.get('data_flags')
    if not isinstance(data_flags, dict):
        errors.append('Response missing "data_flags" dictionary inside "response".')
    else:
        for key, expected in expected_flags.items():
            flag_key = f'{key}_has_data'
            actual = data_flags.get(flag_key)
            if not isinstance(actual, bool):
                errors.append(f'"data_flags.{flag_key}" missing or not a boolean.')
            elif actual != expected:
                errors.append(
                    f'"data_flags.{flag_key}"={actual} but expected {expected} '
                    f'based on supplied results.'
                )

    final_exec = response_root.get('Final', {}).get('Executive Summary', '')
    has_missing_data = any(not value for value in expected_flags.values())

    if has_missing_data:
        logger.info('Validation: missing data detected in results payload.')


    # warning_text = '**IMPORTANT: No Data Provided**'
    # if has_missing_data:
    #     if not isinstance(final_exec, str) or not final_exec.strip().startswith(warning_text):
    #         errors.append('Final Executive Summary must begin with "**IMPORTANT: No Data Provided**".')
    # else:
    #     if isinstance(final_exec, str) and warning_text in final_exec:
    #         errors.append('Warning "**IMPORTANT: No Data Provided**" present despite data being available.')

    return errors


def _results_has_data_map(results: Mapping[str, Any]) -> Dict[str, bool]:
    return {key: bool(results.get(key)) for key in RESULT_KEYS}


def main() -> None:
    pass

    # load_dotenv()

    # parser = argparse.ArgumentParser(description='Call OpenAI to summarise RBSA outputs.')
    # parser.add_argument(
    #     '--model',
    #     default=DEFAULT_MODEL,
    #     help='Model identifier to use (default: %(default)s)',
    # )
    # parser.add_argument(
    #     '--project-root',
    #     type=Path,
    #     default=None,
    #     help='Optional override for the project root directory.',
    # )
    # args = parser.parse_args()

    # result = run_llm(model=args.model, project_root=args.project_root)

    # print(json.dumps(result, indent=2))


if __name__ == '__main__':

    main()

#__all__ = ['rbsa_summarize_results', 'run_llm', 'DEFAULT_MODEL']
