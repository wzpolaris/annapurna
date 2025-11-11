from __future__ import annotations

import time
from typing import Iterable

from . import ScriptIteration, all_iterations


def simulate_typing(text: str, typing_delay: float = 0.04) -> None:
    for char in text:
        print(char, end='', flush=True)
        time.sleep(max(typing_delay, 0.0))
    print(flush=True)


def simulate_submit(submit_delay: float = 0.2) -> None:
    if submit_delay and submit_delay > 0:
        time.sleep(submit_delay)
    print("[enter]\n", flush=True)


def render_dialogue(
    iterations: Iterable[ScriptIteration],
    user_prefix: str = "User: ",
    assistant_prefix: str = "Assistant: ",
    default_delay: float = 0.8,
    typing_delay: float = 0.035,
    submit_delay: float = 0.2,
) -> None:
    delay = max(default_delay, 0.0)

    for index, iteration in enumerate(iterations, start=1):
        for card in iteration.cards:
            user_text = card.get('userText', '')
            if user_text:
                simulate_typing(f"{user_prefix}{user_text}", typing_delay)
                simulate_submit(submit_delay)
                time.sleep(delay)

            for block in card.get('assistantBlocks', []) or []:
                content = block.get('content', '')
                if content:
                    simulate_typing(f"{assistant_prefix}{content}", typing_delay)

        turn_delay = iteration.delay if iteration.delay is not None else delay
        if turn_delay and turn_delay > 0:
            time.sleep(turn_delay)

        print(f"-- iteration {index} complete --\n", flush=True)


def main() -> None:
    render_dialogue(all_iterations())


if __name__ == "__main__":
    main()
