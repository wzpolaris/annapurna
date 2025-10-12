from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from dotenv import load_dotenv
from openai import OpenAI

from .chat_template_rbsa import RESULT_KEYS, build_messages

USE_MOCK_DATA = False

DEFAULT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-5')


def _mock_results() -> Mapping[str, Any]:
    return {
        'results_final': {},
        'results_desmoothing': {},
        'results_approach_A': {},
        'results_approach_B': {},
        'results_approach_C': {},
        'results_approach_D': {},
        'results_substitution': {},
    }


def _load_results(project_root: Path | None) -> Mapping[str, Any]:
    if USE_MOCK_DATA:
        print('Using mock RBSA results payload.')
        return _mock_results()

    try:
        from .rbsa.rbsa_pipeline import rbsa_main

        pipeline_output = rbsa_main()
        analysis_results = pipeline_output.get('analysis_results', {})
        process_results = analysis_results.get('results_process', {})

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
        print(f'RBSA pipeline execution failed: {exc}')
        print('Falling back to mock results payload.')
        return _mock_results()


def _results_has_data_map(results: Mapping[str, Any]) -> Dict[str, bool]:
    return {key: bool(results.get(key)) for key in RESULT_KEYS}


def _validate_response(
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
    warning_text = '**IMPORTANT: No Data Provided**'
    if has_missing_data:
        if not isinstance(final_exec, str) or not final_exec.strip().startswith(warning_text):
            errors.append('Final Executive Summary must begin with "**IMPORTANT: No Data Provided**".')
    else:
        if isinstance(final_exec, str) and warning_text in final_exec:
            errors.append('Warning "**IMPORTANT: No Data Provided**" present despite data being available.')

    return errors


def _request_openai(
    messages: Sequence[Mapping[str, str]],
    *,
    model: str,
) -> Mapping[str, Any]:
    client = OpenAI()

    def parse_json(text: str) -> dict[str, Any]:
        return json.loads(text)

    try:
        responses_result = client.responses.create(
            model=model,
            input=messages,
            response_format={'type': 'json_object'},
        )
        return parse_json(responses_result.output_text)
    except (TypeError, AttributeError):
        chat_messages: Sequence[dict[str, str]] = [
            {'role': message['role'], 'content': message['content']}
            for message in messages
        ]
        try:
            chat_response = client.chat.completions.create(
                model=model,
                messages=chat_messages,
                response_format={'type': 'json_object'},
            )
        except TypeError:
            chat_response = client.chat.completions.create(
                model=model,
                messages=chat_messages,
            )
        content = chat_response.choices[0].message.content or '{}'
        return parse_json(content)


def summarize_results(
    results_payload: Mapping[str, Any],
    *,
    model: str | None = None,
    project_root: Path | None = None,
) -> Mapping[str, Any]:
    model = model or DEFAULT_MODEL
    messages = build_messages(project_root=project_root, results=results_payload)
    try:
        response_payload = _request_openai(messages, model=model)
    except Exception as exc:  # pragma: no cover - network failure
        return {'error': f'OpenAI request failed: {exc}'}

    validation_errors = _validate_response(results_payload, response_payload)
    if validation_errors:
        return {
            'validation_errors': validation_errors,
            'response': response_payload
        }

    return {'response': response_payload}


def run_llm(model: str, project_root: Path | None = None) -> Mapping[str, Any]:
    results_payload = _load_results(project_root)
    summary = summarize_results(results_payload, model=model, project_root=project_root)
    if 'response' in summary:
        summary['results_payload'] = results_payload
    return summary



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


__all__ = ['summarize_results', 'run_llm', 'DEFAULT_MODEL']
