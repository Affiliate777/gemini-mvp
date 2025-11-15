#!/bin/bash
set -euo pipefail

# Always run inside the repo root
REPO_ROOT="/Users/bretbarnard/Projects/gemini-mvp"
cd "$REPO_ROOT"

LOGDIR="$REPO_ROOT/var"
mkdir -p "$LOGDIR"

PORT="${1:-8001}"
PY="$REPO_ROOT/.venv/bin/python"

echo "Starting telemetry.health_server on port $PORT using $PY" >> "$LOGDIR/telemetry_server.log"

nohup "$PY" -m telemetry.health_server --port "$PORT" \
  >> "$LOGDIR/telemetry_server.log" \
  2>> "$LOGDIR/telemetry_server.err" &
echo $!
