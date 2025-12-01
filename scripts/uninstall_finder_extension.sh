#!/usr/bin/env bash
set -euo pipefail

EXT_ID="<EXT_ID>"   # REPLACE: your extension bundle identifier

echo "Disabling extension..."
/usr/bin/pluginkit -e deny -i "$EXT_ID" || true

echo "Unregistering plugin (best-effort)..."
/usr/bin/pluginkit -r "$EXT_ID" || true

echo "Uninstall script finished."
