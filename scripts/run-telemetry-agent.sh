#!/bin/bash
set -euo pipefail

REPO_ROOT="/Users/bretbarnard/Projects/gemini-mvp"
cd "$REPO_ROOT"

LOGDIR="$REPO_ROOT/var"
mkdir -p "$LOGDIR"

PY="$REPO_ROOT/.venv/bin/python"
INTERVAL="${1:-30}"   # seconds between heartbeats

echo "[`date -u +%Y-%m-%dT%H:%M:%SZ`] Starting telemetry agent loop (interval=${INTERVAL}s) using ${PY}" >> "$LOGDIR/telemetry_agent.log"

# Loop in foreground so launchd supervises this process
while true; do
  echo "[`date -u +%Y-%m-%dT%H:%M:%SZ`] Running agent once" >> "$LOGDIR/telemetry_agent.log"
  "$PY" -u -m telemetry.agent --dir "$REPO_ROOT/var" --verbose >> "$LOGDIR/telemetry_agent.log" 2>>"$LOGDIR/telemetry_agent.err" || echo "[`date -u +%Y-%m-%dT%H:%M:%SZ`] agent run failed" >> "$LOGDIR/telemetry_agent.err"
  sleep "$INTERVAL"
done
