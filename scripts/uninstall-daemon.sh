#!/usr/bin/env bash
set -euo pipefail
PLIST="$HOME/Library/LaunchAgents/com.gemini.daemon.plist"
echo "Unloading and removing $PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
echo "Done. You may also remove logs or ledger manually if desired."
