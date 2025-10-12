from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .chat_router import ROUTER_STATE, process_message

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def chat_loop() -> None:
    print('RBSA Chat Router Console. Type "quit" or "exit" to leave.\n')
    while True:
        try:
            user_input = input('You> ').strip()
        except (KeyboardInterrupt, EOFError):
            print('\nGoodbye.')
            return

        if user_input.lower() in {'quit', 'exit'}:
            print('Goodbye.')
            return

        if not user_input:
            continue

        response = process_message(user_input)

        print(f'\nRouter>\n{response}\n')


def main() -> None:
    load_dotenv()
    configure_router_from_env()
    chat_loop()


if __name__ == '__main__':

    sys.exit(main())
