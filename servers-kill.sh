#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="frontend"
BACKEND_DIR="backend"

# Gracefully stop existing processes listening on 5173 (Vite), 4000 (Express), 8000 (FastAPI)
for PORT in 5173 4000 8000; do
  PID=$(lsof -ti tcp:"$PORT" || true)
  if [[ -n "${PID}" ]]; then
    echo "Killing process on port ${PORT} (PID: ${PID})"
    # PID can contain multiple lines; kill each process individually
    kill $PID || true

    # Wait for processes to exit cleanly; force kill if needed
    for attempt in {1..10}; do
      REMAINING=$(lsof -ti tcp:"$PORT" || true)
      if [[ -z "${REMAINING}" ]]; then
        break
      fi
      if [[ "${attempt}" -eq 10 ]]; then
        echo "Force killing stubborn process on port ${PORT} (PID: ${REMAINING})"
        kill -9 $REMAINING || true
      else
        sleep 0.5
      fi
    done
  fi
done

echo "done."
