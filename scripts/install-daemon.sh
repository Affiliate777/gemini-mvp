#!/usr/bin/env bash
set -euo pipefail
USER_HOME="${HOME}"
REPO_ROOT="${USER_HOME}/Projects/gemini-mvp"
VE_PY="${REPO_ROOT}/venv/bin/python"
PLIST="${HOME}/Library/LaunchAgents/com.gemini.daemon.plist"
LOG_OUT="${HOME}/Library/Logs/gemini-daemon.out.log"
LOG_ERR="${HOME}/Library/Logs/gemini-daemon.err.log"
DAEMON_PY="${REPO_ROOT}/cli/daemon.py"

if [ ! -x "${VE_PY}" ]; then
  cat <<MSG
venv python not found at ${VE_PY}
Create venv and install deps:
  cd ${REPO_ROOT}
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
MSG
  exit 1
fi

echo "Writing LaunchAgent to: ${PLIST}"
mkdir -p "$(dirname "${PLIST}")"
cat > "${PLIST}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.gemini.daemon</string>
  <key>ProgramArguments</key>
  <array>
    <string>${VE_PY}</string>
    <string>${DAEMON_PY}</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key>
  <string>${LOG_OUT}</string>
  <key>StandardErrorPath</key>
  <string>${LOG_ERR}</string>
</dict>
</plist>
PLIST

echo "Ensuring log dir exists"
mkdir -p "$(dirname "${LOG_OUT}")"
touch "${LOG_OUT}" "${LOG_ERR}"
chmod 600 "${LOG_OUT}" "${LOG_ERR}" || true

echo "Loading LaunchAgent (will replace existing if loaded)"
launchctl unload "${PLIST}" 2>/dev/null || true
launchctl load "${PLIST}"

echo "Done. Check logs with: tail -f ${LOG_OUT}"
