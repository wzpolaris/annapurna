from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
from typing import Optional


def convert_video(webm_path: str, ffmpeg_path: Optional[str], output_dir: Optional[Path] = None) -> Optional[str]:
    if not ffmpeg_path:
        return None

    webm_file = Path(webm_path)
    candidate = Path(ffmpeg_path).expanduser()

    if candidate.is_dir():
        candidate = candidate / "ffmpeg"

    if candidate.is_file() and os.access(candidate, os.X_OK):
        executable = candidate
    else:
        resolved = shutil.which(str(candidate))
        if not resolved:
            print(
                f"FFmpeg not found at '{ffmpeg_path}'. Skipping MP4 conversion.",
                flush=True,
            )
            return None
        executable = Path(resolved)

    target_dir = output_dir if output_dir is not None else webm_file.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    mp4_file = target_dir / f"{webm_file.stem}.mp4"

    command = [
        str(executable),
        "-y",
        "-i",
        str(webm_file),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        str(mp4_file),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
        print(
            f"FFmpeg conversion failed (exit code {exc.returncode}). See logs for details.",
            flush=True,
        )
        if stderr:
            print(stderr.strip(), flush=True)
        return None

    return str(mp4_file)
