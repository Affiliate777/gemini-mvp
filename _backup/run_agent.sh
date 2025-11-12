#!/usr/bin/env bash
cd "$(dirname "$0")"

# Re-export site/project/push token if already present in env
[ -n "${TELEMETRY_SITE:-}" ] && export TELEMETRY_SITE
[ -n "${TELEMETRY_PROJECT:-}" ] && export TELEMETRY_PROJECT
[ -n "${TELEMETRY_PUSH_TOKEN:-}" ] && export TELEMETRY_PUSH_TOKEN

NODE=${1:-local-node}
INTERVAL=${2:-30}
PUSH=0
for arg in "$@"; do
  if [ "$arg" = "--push" ]; then PUSH=1; fi
done

if [ "$PUSH" -eq 1 ]; then
  exec python3 telemetry.py scheduler "$NODE" "$INTERVAL" --push
else
  exec python3 telemetry.py scheduler "$NODE" "$INTERVAL"
fi
