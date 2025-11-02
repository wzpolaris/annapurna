#!/bin/bash

# Production-ready startup script for multi-worker uvicorn/gunicorn
# This avoids logging race conditions by using proper logging configuration

echo "Starting Northfield Backend with Multi-Worker Logging..."

# Create logs directory
mkdir -p logs

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "uvicorn backend.app.main:app" || true
pkill -f "python -m uvicorn backend.app.main:app" || true

sleep 2

# Production deployment options:

echo "Choose deployment option:"
echo "1. Single worker (development)"
echo "2. Multi-worker Uvicorn (small scale)"
echo "3. Gunicorn with Uvicorn workers (production)"

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "Starting single worker..."
        # Single worker - no race condition concerns
        uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
        ;;
    2)
        echo "Starting multi-worker Uvicorn..."
        # Multi-worker Uvicorn - logs will be separated by PID
        uvicorn backend.app.main:app --workers 4 --host 0.0.0.0 --port 8000
        ;;
    3)
        echo "Starting Gunicorn with Uvicorn workers..."
        # Production setup with Gunicorn
        gunicorn backend.app.main:app \
            --workers 4 \
            --worker-class uvicorn.workers.UvicornWorker \
            --bind 0.0.0.0:8000 \
            --access-logfile logs/gunicorn-access.log \
            --error-logfile logs/gunicorn-error.log \
            --log-level info \
            --daemon
        
        echo "Backend started with PID: $(cat gunicorn.pid)"
        echo "Check logs in:"
        echo "  - logs/gunicorn-access.log"
        echo "  - logs/gunicorn-error.log"
        echo "  - logs/fastapi-*.log (per worker)"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac