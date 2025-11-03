from __future__ import annotations

from pathlib import Path
from datetime import datetime
import sys
import time
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from playwright.sync_api import Page, sync_playwright

from video_script import ScriptIteration, all_iterations
import simulation.config as default_config
from simulation.tools.convert_video import convert_video
from simulation.tools.type_like_human import type_like_human, wpm_to_delay_ms


URL = default_config.DEFAULT_URL
INPUT_SELECTOR = default_config.DEFAULT_INPUT_SELECTOR
SUBMIT_SELECTOR = default_config.DEFAULT_SUBMIT_SELECTOR or None
DEFAULT_WAIT_MS = max(int(default_config.DEFAULT_WAIT_MS), 0)
RESPONSE_SETTLE_MS = max(int(getattr(default_config, 'DEFAULT_RESPONSE_SETTLE_MS', 500)), 0)
ASSISTANT_SELECTOR = getattr(default_config, 'DEFAULT_ASSISTANT_SELECTOR', None)
if ASSISTANT_SELECTOR:
    ASSISTANT_SELECTOR = ASSISTANT_SELECTOR.strip() or None
ASSISTANT_TIMEOUT_MS = max(int(getattr(default_config, 'DEFAULT_ASSISTANT_TIMEOUT_MS', 8000)), 0)
PENDING_SELECTOR = getattr(default_config, 'DEFAULT_PENDING_SELECTOR', None)
if PENDING_SELECTOR:
    PENDING_SELECTOR = PENDING_SELECTOR.strip() or None
WAIT_TO_SUBMIT_MS = max(int(getattr(default_config, 'DEFAULT_WAIT_TO_SUBMIT_MS', 0)), 0)
HEADLESS = bool(default_config.DEFAULT_HEADLESS)
BROWSER = default_config.DEFAULT_BROWSER
KEEP_OPEN = bool(default_config.DEFAULT_KEEP_OPEN)
WEBM_DIR = default_config.DEFAULT_WEBM_DIR or None
MP4_DIR = default_config.DEFAULT_MP4_DIR or None
FFMPEG_PATH = default_config.DEFAULT_FFMPEG_PATH or None

TYPING_MODE = (getattr(default_config, 'DEFAULT_TYPING_MODE', 'auto') or 'auto').strip().lower()
AUTO_TYPING_WPM = 44.0
LOOP_ITERATIONS = max(int(getattr(default_config, 'DEFAULT_LOOP_ITERATIONS', 1)), 0)

SHOW_THINKING = bool(getattr(default_config, 'DEFAULT_THINKING_ENABLED', False))
THINKING_MESSAGE = getattr(default_config, 'DEFAULT_THINKING_MESSAGE', 'Assistant is thinking…')


def _timestamped_name(prefix: str, suffix: str) -> str:
    timestamp = datetime.utcnow().isoformat(sep=" ", timespec="microseconds")
    safe = timestamp.replace(":", "_").replace("-", "_")
    if "." in safe:
        head, frac = safe.split(".", 1)
        safe = f"{head}_{frac[:3]}"
    return f"{prefix}_{safe}.{suffix}"


def _show_thinking_indicator(page: Page, wait_ms: int) -> None:
    if not SHOW_THINKING or wait_ms <= 0:
        return

    payload = {"message": THINKING_MESSAGE, "ms": int(wait_ms)}
    page.evaluate(
        """
        (payload) => {
            const existing = document.getElementById('simulation-thinking-indicator');
            if (existing) {
                existing.remove();
            }

            const indicator = document.createElement('div');
            indicator.id = 'simulation-thinking-indicator';
            indicator.textContent = payload.message;
            indicator.setAttribute('role', 'status');
            indicator.style.position = 'fixed';
            indicator.style.right = '20px';
            indicator.style.bottom = '24px';
            indicator.style.padding = '10px 18px';
            indicator.style.borderRadius = '999px';
            indicator.style.background = 'rgba(37, 99, 235, 0.12)';
            indicator.style.color = '#1f2937';
            indicator.style.fontFamily = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            indicator.style.fontSize = '14px';
            indicator.style.letterSpacing = '0.01em';
            indicator.style.boxShadow = '0 12px 35px rgba(15, 23, 42, 0.18)';
            indicator.style.zIndex = '2147483647';
            indicator.style.pointerEvents = 'none';

            document.body.appendChild(indicator);

            window.setTimeout(() => {
                const element = document.getElementById('simulation-thinking-indicator');
                if (element) {
                    element.remove();
                }
            }, payload.ms);
        }
        """,
        payload,
    )


def _type_text_simple(page: Page, text: str, delay_ms: float) -> None:
    pace = max(delay_ms, 0.0)
    for ch in text:
        if ch == "\r":
            continue
        if ch == "\n":
            page.keyboard.press("Shift+Enter")
            if pace:
                page.wait_for_timeout(pace)
            continue
        page.keyboard.type(ch, delay=pace)


def _type_user_message(page: Page, message: str) -> None:
    field = page.locator(INPUT_SELECTOR).first
    field.wait_for(state="visible")
    field.click()
    field.fill("")

    if TYPING_MODE == "realistic":
        type_like_human(
            page,
            INPUT_SELECTOR,
            message,
        )
    else:
        delay_ms = wpm_to_delay_ms(AUTO_TYPING_WPM)
        _type_text_simple(page, message, delay_ms)
        time.sleep(0.25)

    if WAIT_TO_SUBMIT_MS:
        page.wait_for_timeout(WAIT_TO_SUBMIT_MS)

    if SUBMIT_SELECTOR:
        page.locator(SUBMIT_SELECTOR).click()
    else:
        page.keyboard.press("Enter")


def _wait_for_response(page: Page, iteration: ScriptIteration) -> None:
    wait_ms = DEFAULT_WAIT_MS
    if iteration.delay is not None:
        wait_ms = int(max(iteration.delay * 1000, 0))
    if wait_ms:
        _show_thinking_indicator(page, wait_ms)
        page.wait_for_timeout(wait_ms)

    if PENDING_SELECTOR and ASSISTANT_TIMEOUT_MS:
        try:
            page.wait_for_function(
                "selector => document.querySelectorAll(selector).length === 0",
                arg=PENDING_SELECTOR,
                timeout=ASSISTANT_TIMEOUT_MS,
            )
        except Exception:
            pass

    if ASSISTANT_SELECTOR and ASSISTANT_TIMEOUT_MS:
        try:
            page.wait_for_function(
                "selector => document.querySelector(selector) !== null",
                arg=ASSISTANT_SELECTOR,
                timeout=ASSISTANT_TIMEOUT_MS,
            )
        except Exception:
            pass

    if RESPONSE_SETTLE_MS:
        page.wait_for_timeout(RESPONSE_SETTLE_MS)

    _wait_for_focus_return(page)


def _wait_for_focus_return(page: Page) -> None:
    if not INPUT_SELECTOR:
        return

    while True:
        try:
            is_focused = page.evaluate(
                "selector => { const el = document.querySelector(selector); return el && document.activeElement === el; }",
                INPUT_SELECTOR,
            )
            if is_focused:
                return
        except Exception:
            pass
        time.sleep(0.2)


def replay_script(iterations: Iterable[ScriptIteration]) -> None:
    video_path: Optional[str] = None
    with sync_playwright() as playwright:
        browser_launcher = getattr(playwright, BROWSER)
        browser = browser_launcher.launch(headless=HEADLESS)
        context_kwargs = {}
        webm_filename = None
        target_webm_path: Optional[Path] = None
        if WEBM_DIR:
            webm_base = Path(WEBM_DIR).expanduser()
            webm_base.mkdir(parents=True, exist_ok=True)
            webm_filename = _timestamped_name("video", "webm")
            target_webm_path = webm_base / webm_filename
            context_kwargs["record_video_dir"] = str(webm_base)
            context_kwargs["record_video_size"] = {"width": 1280, "height": 720}
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.goto(URL)

        cycle = 0
        try:
            while True:
                for iteration in iterations:
                    if iteration.user:
                        _type_user_message(page, iteration.user)
                    _wait_for_response(page, iteration)

                cycle += 1
                if LOOP_ITERATIONS and cycle >= LOOP_ITERATIONS:
                    break
        except KeyboardInterrupt:
            print("Interrupted by user; closing browser.", flush=True)

        if KEEP_OPEN:
            print(
                "Simulation complete. Browser window left open. "
                "Press Enter (or Ctrl+C) here to close.",
                flush=True,
            )
            try:
                input()
            except KeyboardInterrupt:
                pass

        context.close()
        browser.close()

        if target_webm_path and page.video:
            try:
                raw_path = Path(page.video.path())
                final_webm = target_webm_path
                raw_path.rename(final_webm)
                video_path = str(final_webm)
            except Exception:
                video_path = None

    if video_path:
        print(f"Video saved to: {video_path}", flush=True)
        if MP4_DIR:
            mp4_dir_path = Path(MP4_DIR).expanduser()
            mp4_dir_path.mkdir(parents=True, exist_ok=True)
        else:
            mp4_dir_path = None
        mp4_path = convert_video(video_path, FFMPEG_PATH, mp4_dir_path)
        if mp4_path:
            print(f"MP4 saved to: {mp4_path}", flush=True)


def main() -> None:
    iterations = all_iterations()
    if not iterations:
        raise SystemExit("No scripted iterations found. Define iter_*.py files in video_script/")
    replay_script(iterations)


if __name__ == "__main__":
    main()
