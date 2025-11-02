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

# (
#   #cd "${BACKEND_DIR}"
#   echo "Starting FastAPI backend (logs: ../logs/fastapi.log)..."
#   nohup uvicorn backend.app.main:app --reload > ./logs/fastapi.log 2>&1 &
# )

echo "All services launched. Check ./logs/*.log for output."
echo "Frontend (Vite in dev): http://localhost:5173"
echo "Proxy (Express): http://localhost:4000"
echo "Backend (FastAPI): http://localhost:8000/docs"
