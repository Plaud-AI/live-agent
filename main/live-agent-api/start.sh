#!/bin/bash
set -e

echo "=========================================="
echo "Live Agent API Startup"
echo "=========================================="

# Wait for database to be ready (with retry)
echo "[1/3] Waiting for database connection..."
MAX_RETRIES=30
RETRY_INTERVAL=2

for i in $(seq 1 $MAX_RETRIES); do
    if .venv/bin/python -c "
import asyncio
import asyncpg
import os
import re

async def check():
    url = os.environ.get('DATABASE_URL', '')
    dsn = re.sub(r'^postgresql\+asyncpg://', 'postgresql://', url)
    conn = await asyncpg.connect(dsn, timeout=5)
    await conn.close()
    return True

asyncio.run(check())
" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    
    if [ $i -eq $MAX_RETRIES ]; then
        echo "ERROR: Database connection failed after $MAX_RETRIES attempts"
        exit 1
    fi
    
    echo "Waiting for database... (attempt $i/$MAX_RETRIES)"
    sleep $RETRY_INTERVAL
done

# Run database migrations
echo "[2/3] Running database migrations..."
.venv/bin/python scripts/migrate.py

# Start the application
echo "[3/3] Starting uvicorn server..."
exec .venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8080
