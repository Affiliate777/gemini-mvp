set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/update-audit.log"

VERSION="${1:-${VERSION:-}}"
RELEASE_DIR="${2:-${RELEASE_DIR:-}}"
RC="${3:-}"

TS="$(date +%s)"
_escape_json() {
  local s="$1"
  s="${s//$'\n'/ }"                 # replace newlines with space
  s="${s//\\/\\\\}"                # backslash -> \\
  s="${s//\"/\\\"}"                # " -> \"
  printf '%s' "$s"
}

V_ESC="$(_escape_json "${VERSION:-}")"
R_ESC="$(_escape_json "${RELEASE_DIR:-}")"

if [ -n "$RC" ]; then
  printf '{"version":"%s","release_dir":"%s","rc":%s,"ts":%s}\n' "$V_ESC" "$R_ESC" "$RC" "$TS" >> "$LOG_FILE"
else
  printf '{"version":"%s","release_dir":"%s","ts":%s}\n' "$V_ESC" "$R_ESC" "$TS" >> "$LOG_FILE"
fi

exit 0
