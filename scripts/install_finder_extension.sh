#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
BUILD_DIR="$ROOT/build/Build/Products/Debug"
EXT_ID="<EXT_ID>"   # REPLACE: your extension bundle identifier

APPEX=$(find "$BUILD_DIR" -name "*.appex" -print -quit)

if [[ -z "$APPEX" ]]; then
  echo "Error: .appex not found in $BUILD_DIR. Build first with xcodebuild."
  exit 1
fi

echo "Installing FinderSync extension from: $APPEX"
/usr/bin/pluginkit -i "$APPEX"
echo "Trying to enable extension (may require user action in System Settings)..."
/usr/bin/pluginkit -e use -i "$EXT_ID" || true
echo "Install script finished. If extension is not active, enable it at System Settings -> Extensions -> Finder Extensions."
