# Simulation Harness

This folder contains a Playwright runner that replays the scripted
conversation using the turns defined in `video_script/iter_*.py`.

## Prerequisites

1. Install dependencies:
   ```bash
   pip install playwright
   playwright install
   ```
2. Start the web application you want to drive (e.g. the Mantine UI).

## Configure Defaults

Edit `simulation/config.py` with your preferred URL, CSS selectors, and
timing options. Once the defaults match your environment you can usually run
the simulation without any command-line arguments.

To enable automatic MP4 conversion, place an `ffmpeg` binary in
`simulation/tools/ffmpeg` (or set `DEFAULT_FFMPEG_PATH` to wherever FFmpeg
is installed). Recorded sessions are saved under `simulation/output/webm`
and `simulation/output/mp4`. Each capture is named using an ISO timestamp,
e.g. `video_2025_11_02 18_05_12_345.webm`.

Typing behaviour is controlled via `DEFAULT_TYPING_MODE` (`"auto"` or
`"realistic"`). In realistic mode the helper script adds uneven timing, typos, and backspaces;
set `DEFAULT_TYPING_MODE` to `"auto"` for steady playback or tweak `type_like_human.py` for custom cadence.
Enable `DEFAULT_THINKING_ENABLED` to overlay a subtle "Assistant is thinking…" badge during the wait interval (`DEFAULT_WAIT_MS`).
Use `DEFAULT_RESPONSE_SETTLE_MS` to add a small buffer after the backend delay so the UI finishes rendering before the next scripted turn.
If your UI exposes stable selectors, set `DEFAULT_ASSISTANT_SELECTOR` so the simulator can
detect when a new assistant card arrives, and `DEFAULT_PENDING_SELECTOR` so it waits until
any loading indicator (e.g., the `AssistantPending` component) disappears before proceeding.
Use `DEFAULT_ASSISTANT_TIMEOUT_MS` to cap how long those waits last.
Set `DEFAULT_LOOP_ITERATIONS` to control whether the scripted turns repeat; `0` loops indefinitely
until you stop the harness, while a positive value limits the number of full conversation cycles.
`DEFAULT_WAIT_TO_SUBMIT_MS` inserts a short hesitation between finishing typing and pressing the
send button, so it looks like the user pauses before submitting.

## Running the Simulation

Once the defaults are set, simply run:

```bash
python simulation/run_simulation.py
```

The runner reads every option from `simulation/config.py`, so there are no
command-line flags. Adjust the config file to tweak typing speed, delays,
headless mode, video output, or ffmpeg location.

The script imports `video_script.all_iterations()` so updates to the
iteration files automatically flow into the simulation.
