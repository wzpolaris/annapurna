"""
Utilities to mimic human typing behaviour in Playwright-driven simulations.
"""

from __future__ import annotations

import math
import random
import time
from typing import Iterable, Optional, Tuple

from mistune import html
from playwright.sync_api import Page

AVERAGE_CHARS_PER_WORD = 5
TYPING_CHUNK_SIZE = 3

TYPING_WPM_BASE = 200.0
TYPING_WPM_MIN_MAX = (182.0, 232.0)
TYPING_HUMAN_PAUSE_PROB = 0.08
TYPING_HUMAN_PAUSE_RANGE = (0.05, 0.2)
TYPING_ERROR_RATE = 0.04
TYPING_CORRECTION_PROB = 0.9
TYPING_BURST_PROB = 0.18
TYPING_PUNCTUATION_PAUSE_PROB = 0.25


# Simple QWERTY adjacency map used to generate plausible mistakes
KEY_NEIGHBORS = {
    "a": "qwsz",
    "b": "vghn",
    "c": "xdfv",
    "d": "ersfcx",
    "e": "wsdr",
    "f": "rtgdvc",
    "g": "tyfhvb",
    "h": "yugjnb",
    "i": "ujko",
    "j": "uikhmn",
    "k": "ijolm,",
    "l": "op;k.",
    "m": "njk,",
    "n": "bhjm",
    "o": "iklp",
    "p": "ol;[",
    "q": "wa",
    "r": "edft",
    "s": "wedxz",
    "t": "rfgy",
    "u": "yhji",
    "v": "cfgb",
    "w": "qase",
    "x": "zsdc",
    "y": "tghu",
    "z": "asx",
    "1": "2q",
    "2": "13w",
    "3": "24e",
    "4": "35r",
    "5": "46t",
    "6": "57y",
    "7": "68u",
    "8": "79i",
    "9": "80o",
    "0": "9p",
}


def lognorm_delay(mean_ms: float = 80.0, sigma: float = 0.6) -> float:
    """Return a random key delay (seconds) drawn from a log-normal distribution."""
    mean_ms = max(mean_ms, 12.0)
    mu = math.log(mean_ms) - (sigma**2) / 2
    return max(8, random.lognormvariate(mu, sigma)) / 1000.0


def human_pause(prob: float = TYPING_HUMAN_PAUSE_PROB) -> None:
    if random.random() < prob:
        time.sleep(random.uniform(*TYPING_HUMAN_PAUSE_RANGE))


def maybe_typo(ch: str, typo_rate: float = TYPING_ERROR_RATE) -> Optional[str]:
    """Return a neighbouring key as a typo or None."""
    neighbours = KEY_NEIGHBORS.get(ch.lower())
    if neighbours and random.random() < typo_rate:
        return random.choice(neighbours)
    return None


def wpm_to_delay_ms(words_per_minute: float) -> float:
    """Convert words per minute into an average delay per character in milliseconds."""
    wpm = max(words_per_minute, 1.0)
    chars_per_minute = wpm * AVERAGE_CHARS_PER_WORD
    return max(20.0, 60_000.0 / chars_per_minute)


def _chunked_wpm(target_range: Tuple[float, float], chunk_size: int) -> Iterable[float]:
    """Yield WPM samples for each chunk."""
    low, high = target_range
    while True:
        yield max(6.0, random.uniform(low, high))


def type_like_human(
    page: Page,
    selector: str,
    text: str,
    *,
    base_wpm: float = TYPING_WPM_BASE,
    wpm_range: Tuple[float, float] = TYPING_WPM_MIN_MAX,
    chunk_size: int = TYPING_CHUNK_SIZE,
    typo_rate: float = TYPING_ERROR_RATE,
    correction_prob: float = TYPING_CORRECTION_PROB,
    burst_prob: float = TYPING_BURST_PROB,
    punctuation_pause_prob: float = TYPING_PUNCTUATION_PAUSE_PROB,
) -> None:
    """
    Click the field identified by selector and type the text with uneven speed,
    bursts, occasional typos, and backspaces.
    """

    locator = page.locator(selector).first
    locator.click()

    composite_iter = _chunked_wpm(wpm_range, chunk_size)
    current_delay_ms = wpm_to_delay_ms(base_wpm)
    last_burst = False

    for idx, ch in enumerate(text):
        if idx % chunk_size == 0:
            sampled_wpm = next(composite_iter)
            current_delay_ms = wpm_to_delay_ms(sampled_wpm)

        if ch in ",.;:?!)]}" and random.random() < punctuation_pause_prob:
            time.sleep(random.uniform(0.2, 0.5))

        burst = (random.random() < burst_prob) and not last_burst
        delay = lognorm_delay(current_delay_ms * (0.6 if burst else 1.0))
        last_burst = burst

        if ch == "\r":
            continue

        if ch == "\n":
            page.keyboard.press("Shift+Enter")
            time.sleep(delay)
            human_pause(prob=0.06)
            continue

        typo = maybe_typo(ch, typo_rate=typo_rate)
        if typo:
            page.keyboard.type(typo, delay=0)
            time.sleep(delay * random.uniform(0.4, 0.9))
            if random.random() < correction_prob:
                page.keyboard.press("Backspace")
                time.sleep(delay * random.uniform(0.6, 1.2))

        page.keyboard.type(ch, delay=0)
        time.sleep(delay)
        human_pause(prob=0.06)

    time.sleep(random.uniform(0.2, 0.6))


if __name__ == "__main__":

    from playwright.sync_api import sync_playwright

    html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Typing Demo</title>
            <style>
            body { font-family: sans-serif; padding: 3rem; background: #f5f6fa; }
            .card { max-width: 480px; margin: 0 auto; background: white; padding: 2rem; border-radius: 16px;
                    box-shadow: 0 18px 40px rgba(15, 23, 42, 0.15); }
            label { display: block; margin-bottom: 0.6rem; font-weight: 600; color: #1f2937; }
            input { width: 100%; padding: 0.8rem 1rem; font-size: 1.1rem; border-radius: 12px;
                    border: 1px solid #d1d5db; outline: none; transition: border-color 0.2s;
                    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05); }
            input:focus { border-color: #2563eb; box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12); }
            .hint { margin-top: 1.4rem; color: #6b7280; font-size: 0.95rem; }
            </style>
        </head>
        <body>
            <div class="card">
            <h2>Human Typing Demo</h2>
            <p>Watch the automation type with uneven cadence, pauses, and typo corrections.</p>
            <label for="chat">Message</label>
            <input id="chat" type="text" placeholder="Type here…" autocomplete="off" />
            <p class="hint">You can tweak the timing via DEFAULT_TYPING_WPM and DEFAULT_TYPING_RANGE.</p>
            </div>
        </body>
        </html>
    """


    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.set_content(html, wait_until="load")

        type_like_human(page, "#chat", "Hello from the human-like typer!")

        try:
            input("Press Enter in the terminal to close the demo browser... ")
        finally:
            context.close()
            browser.close()
