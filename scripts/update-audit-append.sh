#!/usr/bin/env bash
set -euo pipefail
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$BASE_DIR/logs/update-audit.log"
VERSION="${1:-${VERSION:-}}"
RELEASE_DIR="${2:-${RELEASE_DIR:-}}"
TS="$(date +%s)"
_escape_json(){ local s="$1"; s="${s//$'\n'/ }"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '%s' "$s"; }
V_ESC="$(_escape_json "${VERSION:-}")"
R_ESC="$(_escape_json "${RELEASE_DIR:-}")"
# use flock on the log file descriptor (requires util-linux; macOS has /usr/bin/lockfile? if not, fallback to plain append)
( flock -x 200 2>/dev/null || true; printf '{"version":"%s","release_dir":"%s","ts":%s}\n' "$V_ESC" "$R_ESC" "$TS" >> "$LOG_FILE" ) 200>"$LOG_FILE".lock
