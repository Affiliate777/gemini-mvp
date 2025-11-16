
set -euo pipefail
parse_version_from_stdin() {
  local in
  if [ -t 0 ]; then
    in=""
  else
    in="$(cat - 2>/dev/null || true)"
  fi
  printf '%s' "$in" | sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]\+\)".*/\1/p'
}

if [ $# -ge 1 ]; then
  VERSION="$1"
else
  VERSION="$(parse_version_from_stdin || true)"
fi

if [ -z "${VERSION:-}" ]; then
  echo "usage: $0 <version>  OR pipe JSON with {\"version\":\"vX.Y.Z\"} to stdin" >&2
  exit 2
fi

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
UPDATES_DIR="$BASE_DIR/updates/$VERSION"
ART="$UPDATES_DIR/release.tar.gz"
CHK_FILE="$UPDATES_DIR/release.sha256"
RELEASES_DIR="$BASE_DIR/releases"
RELEASE_DIR="$RELEASES_DIR/$VERSION-$(date +%s)"
_exit_status=0
trap '_exit_status=$?; bash "$(dirname "$0")/update-audit-append.sh" "$VERSION" "$RELEASE_DIR" "$_exit_status" || true; exit $_exit_status' EXIT

if [ ! -f "$ART" ]; then
  echo "artifact not found: $ART" >&2
  exit 3
fi
if [ ! -f "$CHK_FILE" ]; then
  echo "checksum file not found: $CHK_FILE" >&2
  exit 4
fi

mkdir -p "$RELEASE_DIR"

expected="$(tr -d '[:space:]' < "$CHK_FILE")"
actual="$(shasum -a 256 "$ART" | awk '{print $1}')"
if [ "$expected" != "$actual" ]; then
  echo "checksum mismatch (expected $expected, got $actual)" >&2
  exit 5
fi

tar -xzf "$ART" -C "$RELEASE_DIR"
mkdir -p "$BASE_DIR/runtime"
ln -sfn "$RELEASE_DIR" "$BASE_DIR/runtime/current"

nohup sh -c '
PROBE_LOG="logs/update-apply.log"
mkdir -p /tmp
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) probe: start" >> "$PROBE_LOG"
for i in 1 2 3 4 5 6 7 8 9 10; do
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt $i: curl --max-time 10" >> "$PROBE_LOG"
  if /usr/bin/env curl -fsS --max-time 10 http://127.0.0.1:8001/health >/dev/null 2>&1; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt $i: success" >> "$PROBE_LOG"
    exit 0
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) attempt $i: fail" >> "$PROBE_LOG"
    sleep 3
  fi
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) probe: giving up" >> "$PROBE_LOG"
exit 1
' >/dev/null 2>&1 &

echo "update applied successfully: $VERSION -> $RELEASE_DIR"

mkdir -p "$BASE_DIR/logs"

exit 0
