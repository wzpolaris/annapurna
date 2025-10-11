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
