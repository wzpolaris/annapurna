"""
Default settings for the Playwright simulation harness.

Update the values below to match the local environment. All options can still
be overridden from the command line, but with these defaults, you can usually
run `python simulation/run_simulation.py` with no arguments.
"""

DEFAULT_URL = "http://localhost:5173"

DEFAULT_INPUT_SELECTOR = 'textarea[data-testid="chat-input"]'
DEFAULT_SUBMIT_SELECTOR = 'button[data-testid="chat-send"]'

DEFAULT_TYPING_MODE: str = "realistic"  # "auto" | "realistic"
DEFAULT_WAIT_MS = 5000

DEFAULT_HEADLESS = False
DEFAULT_BROWSER = "chromium"
DEFAULT_KEEP_OPEN = True

DEFAULT_WEBM_DIR: str | None = "simulation/output/webm"
DEFAULT_MP4_DIR: str | None = "simulation/output/mp4"
DEFAULT_FFMPEG_PATH: str | None = "/opt/homebrew/bin/ffmpeg"
DEFAULT_THINKING_ENABLED = True
DEFAULT_THINKING_MESSAGE = "Assistant is thinking…"
DEFAULT_RESPONSE_SETTLE_MS = 5000
DEFAULT_ASSISTANT_SELECTOR: str | None = '[data-testid="assistant-response"]'
DEFAULT_ASSISTANT_TIMEOUT_MS = 10000
DEFAULT_PENDING_SELECTOR: str | None = '[data-testid="assistant-pending"]'
DEFAULT_WAIT_TO_SUBMIT_MS = 2000
DEFAULT_LOOP_ITERATIONS = 1  # 0 = loop forever, positive value limits cycles
