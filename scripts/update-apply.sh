#!/bin/bash
set -euo pipefail

REPO_ROOT="/Users/bretbarnard/Projects/gemini-mvp"
cd "$REPO_ROOT"

USAGE="Usage: $(basename "$0") <version> [target_dir]"
if [ $# -lt 1 ]; then
  echo "$USAGE" >&2
  exit 2
fi

VERSION="$1"
TARGET="${2:-$REPO_ROOT}"   # by default deploy into repo root for local testing
SRC_DIR="$REPO_ROOT/updates/$VERSION"

if [ ! -d "$SRC_DIR" ]; then
  echo "ERROR: update snapshot not found: $SRC_DIR" >&2
  exit 3
fi

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_DIR="$REPO_ROOT/var/backups/backup_${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

echo "Backing up current target to $BACKUP_DIR"
rsync -a --delete --exclude var --exclude .git "$TARGET/" "$BACKUP_DIR/"

echo "Applying update $VERSION -> $TARGET"
# Use rsync to mirror the update snapshot into the target
rsync -a --delete "$SRC_DIR/" "$TARGET/"

# Record history
HISTORY_FILE="$REPO_ROOT/var/update_history.log"
CURRENT_FILE="$REPO_ROOT/var/current_version.txt"
echo "${TIMESTAMP} ${VERSION} -> ${TARGET}" >> "$HISTORY_FILE"
echo "$VERSION" > "$CURRENT_FILE"

echo "Update applied: $VERSION"
echo "Backup at: $BACKUP_DIR"
exit 0
