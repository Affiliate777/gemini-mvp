#!/bin/bash
set -euo pipefail

REPO_ROOT="/Users/bretbarnard/Projects/gemini-mvp"
cd "$REPO_ROOT"

USAGE="Usage: $(basename "$0") [target_dir]"
TARGET="${1:-$REPO_ROOT}"

HISTORY_FILE="$REPO_ROOT/var/update_history.log"

if [ ! -f "$HISTORY_FILE" ]; then
  echo "No update history found at $HISTORY_FILE" >&2
  exit 2
fi

# Find last 2 applied versions (most recent last line)
LAST_TWO=$(tail -n 2 "$HISTORY_FILE" | awk '{print $2}' || true)
count=$(echo "$LAST_TWO" | wc -w)

if [ "$count" -lt 2 ]; then
  echo "Not enough history to rollback (need at least two entries)." >&2
  tail -n 5 "$HISTORY_FILE"
  exit 3
fi

# Last line is current, previous is second-to-last
CURRENT=$(echo "$LAST_TWO" | tail -n1)
PREVIOUS=$(echo "$LAST_TWO" | head -n1)

if [ -z "$PREVIOUS" ] || [ "$PREVIOUS" = "$CURRENT" ]; then
  echo "Cannot determine previous version to rollback to." >&2
  exit 4
fi

echo "Rolling back from $CURRENT to $PREVIOUS"
# Reuse apply script to re-apply previous version
"$REPO_ROOT/scripts/update-apply.sh" "$PREVIOUS" "$TARGET"
