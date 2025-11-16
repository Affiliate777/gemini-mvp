#!/usr/bin/env bash
cd "$(dirname "$0")"

# default values from environment (may be empty)
SITE="${TELEMETRY_SITE:-}"
PROJECT="${TELEMETRY_PROJECT:-}"
PUSH_TOKEN="${TELEMETRY_PUSH_TOKEN:-}"

# parse positional and named args
NODE="local-node"
INTERVAL="30"
PUSH=0

# consume positional if present
if [ $# -ge 1 ] && [[ ! "$1" =~ ^-- ]]; then
  NODE="$1"
  shift
fi
if [ $# -ge 1 ] && [[ ! "$1" =~ ^-- ]]; then
  INTERVAL="$1"
  shift
fi

# parse flags
while [ $# -gt 0 ]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --site) SITE="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --token) PUSH_TOKEN="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; shift ;;
  esac
done

# export if set
[ -n "$SITE" ] && export TELEMETRY_SITE="$SITE"
[ -n "$PROJECT" ] && export TELEMETRY_PROJECT="$PROJECT"
[ -n "$PUSH_TOKEN" ] && export TELEMETRY_PUSH_TOKEN="$PUSH_TOKEN"

# start scheduler with push flag when requested
if [ "$PUSH" -eq 1 ]; then
  exec python3 telemetry.py scheduler "$NODE" "$INTERVAL" --push
else
  exec python3 telemetry.py scheduler "$NODE" "$INTERVAL"
fi
