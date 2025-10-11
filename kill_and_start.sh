#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

# Gracefully stop existing processes listening on 5173 (Vite), 4000 (Express), 8000 (FastAPI)
for PORT in 5173 4000 8000; do
  PID=$(lsof -ti tcp:"$PORT" || true)
  if [[ -n "${PID}" ]]; then
    echo "Killing process on port ${PORT} (PID: ${PID})"
    kill "${PID}" || true
  fi
done

mkdir -p logs

# Start processes
(
  cd "${FRONTEND_DIR}"
  echo "Starting Vite dev server (logs: ../logs/vite.log)..."
  nohup npm run dev > ../logs/vite.log 2>&1 &
)

(
  cd "${FRONTEND_DIR}"
  echo "Starting Express proxy (logs: ../logs/express.log)..."
  nohup npm run serve > ../logs/express.log 2>&1 &
)

(
  cd "${BACKEND_DIR}"
  echo "Starting FastAPI backend (logs: ../logs/fastapi.log)..."
  nohup uvicorn app.main:app --reload > ../logs/fastapi.log 2>&1 &
)

echo "All services launched. Check ./logs/*.log for output."
