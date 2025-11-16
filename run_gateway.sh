#!/usr/bin/env bash
cd "$(dirname "$0")"
if [ -n "$1" ]; then
  export TELEMETRY_API_TOKEN="$1"
fi
exec .venv/bin/python -m uvicorn api_gateway:app --host 127.0.0.1 --port 8000
