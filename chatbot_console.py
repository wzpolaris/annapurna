from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

from analytics.chat_router_rbsa import process_message

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv()

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

    chat_loop()


if __name__ == '__main__':

    sys.exit(main())
