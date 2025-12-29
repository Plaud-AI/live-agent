#!/bin/bash
set -e

echo "=========================================="
echo "Live Agent API Startup"
echo "=========================================="

# Run database migrations
echo "[1/2] Running database migrations..."
.venv/bin/python scripts/migrate.py

# Start the application
echo "[2/2] Starting uvicorn server..."
exec .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
