#!/usr/bin/env bash
# Production launcher script for Quantum Traffic Route Optimization (Q-TRO)
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================================="
echo " Starting Q-TRO Platform (Egreen Quanta - PS 26137)"
echo "================================================================="

# Detect or create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r backend/requirements.txt
fi

# Ensure dependencies installed
echo "Checking dependencies..."
.venv/bin/pip install -q -r backend/requirements.txt

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WORKERS:-2}"

echo "Starting server on http://${HOST}:${PORT} (Workers: ${WORKERS})..."
exec .venv/bin/uvicorn backend.app.main:app --host "${HOST}" --port "${PORT}" --workers "${WORKERS}"
