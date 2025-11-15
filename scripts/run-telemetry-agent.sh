#!/bin/zsh
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1
AGENT_PY="${REPO_ROOT}/.venv/bin/python"
LOGFILE="${REPO_ROOT}/var/telemetry_agent.log"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "[$timestamp] Starting telemetry agent..." >> "$LOGFILE"
"$AGENT_PY" -m telemetry.agent --dir "${REPO_ROOT}/var" --verbose >> "$LOGFILE" 2>&1
exit $?
