#!/usr/bin/env bash
set -euo pipefail

# scripts/update-audit-append.sh
# Usage: scripts/update-audit-append.sh <version> <release_dir>
# Falls back to environment variables VERSION / RELEASE_DIR if args not supplied.

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update-audit.log"

# Accept args with fallback to env
VERSION="${1:-${VERSION:-}}"
RELEASE_DIR="${2:-${RELEASE_DIR:-}}"

# timestamp as integer seconds since epoch
TS="$(date +%s)"

# POSIX-safe JSON escaping for backslash and double-quote
# (also strip newlines)
_escape_json() {
  local s="$1"
  s="${s//$'\n'/ }"                 # replace newlines with space
  s="${s//\\/\\\\}"                # backslash -> \\
  s="${s//\"/\\\"}"                # " -> \"
  printf '%s' "$s"
}

V_ESC="$(_escape_json "${VERSION:-}")"
R_ESC="$(_escape_json "${RELEASE_DIR:-}")"

printf '{"version":"%s","release_dir":"%s","ts":%s}\n' "$V_ESC" "$R_ESC" "$TS" >> "$LOG_FILE"
exit 0
