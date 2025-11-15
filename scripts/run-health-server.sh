#!/usr/bin/env bash
PORT="${1:-8001}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1
LOGDIR="${REPO_ROOT}/var"
mkdir -p "$LOGDIR"
if [ -x "${REPO_ROOT}/.venv/bin/python" ]; then
  PY="${REPO_ROOT}/.venv/bin/python"
else
  PY="$(command -v python || command -v python3)"
fi
echo "Starting telemetry.health_server on port ${PORT} using ${PY}" >> "${LOGDIR}/telemetry_server.log"
nohup "${PY}" -m telemetry.health_server --port "${PORT}" >> "${LOGDIR}/telemetry_server.log" 2>&1 &
echo $!
