from __future__ import annotations

import time
from typing import Iterable

from . import ScriptIteration, all_iterations


def simulate_typing(text: str, typing_delay: float = 0.04) -> None:
    """Render text character-by-character to mimic typing in a terminal."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(max(typing_delay, 0.0))
    print(flush=True)


def simulate_submit(submit_delay: float = 0.2) -> None:
    """Display an enter key submission cue after a short pause."""
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
    """
    Walk through the scripted dialogue, inserting delays between turns.

    Each ScriptIteration may define its own delay override which is applied
    after the assistant finishes speaking.
    """
    delay = max(default_delay, 0.0)

    for index, iteration in enumerate(iterations, start=1):
        if iteration.user:
            simulate_typing(f"{user_prefix}{iteration.user}", typing_delay)
            simulate_submit(submit_delay)
            time.sleep(delay)

        simulate_typing(f"{assistant_prefix}{iteration.assistant}", typing_delay)

        turn_delay = iteration.delay if iteration.delay is not None else delay
        if turn_delay and turn_delay > 0:
            time.sleep(turn_delay)

        print(f"-- iteration {index} complete --\n", flush=True)


def main() -> None:
    """Play the scripted conversation from start to finish."""
    render_dialogue(all_iterations())


if __name__ == "__main__":
    main()
