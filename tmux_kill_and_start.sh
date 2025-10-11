#!/usr/bin/env bash
set -euo pipefail

if ! command -v tmux >/dev/null 2>&1; then
  echo "tmux is not installed. Please install tmux and rerun this script."
  exit 1
fi

SESSION_NAME="northfield-dev"
FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

if tmux has-session -t "${SESSION_NAME}" 2>/dev/null; then
  echo "Killing existing tmux session ${SESSION_NAME}"
  tmux kill-session -t "${SESSION_NAME}"
fi

echo "Creating new tmux session ${SESSION_NAME}"
tmux new-session -d -s "${SESSION_NAME}" -c "${BACKEND_DIR}" 'uvicorn app.main:app --reload'

echo "Adding bottom pane for Vite dev server"
tmux split-window -v -t "${SESSION_NAME}:0" -c "${FRONTEND_DIR}" 'npm run dev'

echo "Adding top-right pane for Express proxy"
tmux select-pane -t "${SESSION_NAME}:0.0"
tmux split-window -h -t "${SESSION_NAME}:0.0" -c "${FRONTEND_DIR}" 'npm run serve'

tmux select-pane -t "${SESSION_NAME}:0.0"
tmux select-layout -t "${SESSION_NAME}" tiled
tmux display-message "Session ${SESSION_NAME} ready. Attaching..."
tmux attach-session -t "${SESSION_NAME}"
