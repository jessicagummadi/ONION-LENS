#!/bin/bash
set -e

echo "=== [ONION LENS] Starting Web Service on Render ==="
echo "PORT: ${PORT:-8000}"

# Find and use the virtualenv created during build
if [ -f "./.venv/bin/uvicorn" ]; then
    echo "Found uvicorn at ./.venv/bin/uvicorn"
    exec ./.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
elif [ -f "/opt/render/project/src/.venv/bin/uvicorn" ]; then
    echo "Found uvicorn at /opt/render/project/src/.venv/bin/uvicorn"
    exec /opt/render/project/src/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
elif command -v uvicorn >/dev/null 2>&1; then
    echo "Found uvicorn in PATH"
    exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
else
    echo "Virtualenv not found, installing to python3..."
    python3 -m pip install -r requirements.txt
    exec python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
fi
