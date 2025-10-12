from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Mapping

from openai import OpenAI

from .openai_template import build_messages

DEFAULT_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4.1-mini')


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


def run_llm(model: str, project_root: Path | None = None) -> dict[str, Any]:
    messages = build_messages(project_root=project_root, results=_mock_results())

    client = OpenAI()
    response = client.responses.create(
        model=model,
        input=messages,
        response_format={'type': 'json_object'},
    )

    return json.loads(response.output_text)


def main() -> None:
    parser = argparse.ArgumentParser(description='Call OpenAI to summarise RBSA outputs.')
    parser.add_argument(
        '--model',
        default=DEFAULT_MODEL,
        help='Model identifier to use (default: %(default)s)',
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=None,
        help='Optional override for the project root directory.',
    )
    args = parser.parse_args()

    result = run_llm(model=args.model, project_root=args.project_root)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
