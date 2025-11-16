DEPLOY.md

Quickstart
----------
1) Ensure virtualenv is active:
   cd /Users/bretbarnard/Projects/gemini-mvp
   source .venv/bin/activate

2) Start gateway (foreground, no auth):
   ./run_gateway.sh

3) Start gateway with token:
   ./run_gateway.sh gemini123

4) Start agent scheduler (foreground, no push):
   ./run_agent.sh local-node 30

5) Start agent scheduler with push:
   export TELEMETRY_PUSH_TOKEN="gemini123"
   ./run_agent.sh local-node 30 --push

Check status & logs
-------------------
1) Show runtime files:
   ls -la ./runtime/telemetry

2) Tail agent logfile:
   tail -n 200 -f ./runtime/telemetry/logs/agent.log

3) Tail gateway logs:
   tail -n 200 -f ./runtime/telemetry/logs/gateway.out.log
   tail -n 200 -f ./runtime/telemetry/logs/gateway.err.log

4) Inspect local DB:
   sqlite3 ./runtime/telemetry/telemetry.db "SELECT id, node_id, timestamp FROM telemetry ORDER BY id DESC LIMIT 10;"

5) Inspect remote DB:
   sqlite3 ./runtime/telemetry/remote_ingest.db "SELECT id, node_id, timestamp FROM remote_telemetry ORDER BY id DESC LIMIT 10;"

Using launchd (macOS)
---------------------
1) Install launch agents (already installed if you followed setup):
   ls -la ~/Library/LaunchAgents/com.gemini.*.plist

2) Load agents:
   launchctl load ~/Library/LaunchAgents/com.gemini.api_gateway.plist
   launchctl load ~/Library/LaunchAgents/com.gemini.telemetry_agent.plist

3) Unload agents:
   launchctl unload ~/Library/LaunchAgents/com.gemini.api_gateway.plist
   launchctl unload ~/Library/LaunchAgents/com.gemini.telemetry_agent.plist

4) Show loaded:
   launchctl list | grep com.gemini || true

Troubleshooting
---------------
1) "uvicorn: not found" in run_gateway.sh
   Ensure .venv exists and contains uvicorn. Start gateway with venv python:
   .venv/bin/python -m uvicorn api_gateway:app --host 127.0.0.1 --port 8000

2) Port 8000 already in use
   lsof -nP -iTCP:8000 -sTCP:LISTEN
   pkill -f "uvicorn api_gateway:app" || true

3) Push returns 401 Unauthorized
   Ensure gateway expects token and agent has same token:
   export TELEMETRY_API_TOKEN="gemini123"    # for gateway (when starting)
   export TELEMETRY_PUSH_TOKEN="gemini123"   # for agent

4) Heredoc / paste errors when creating files
   Use the exact commands shown in the project root. Avoid pasting extra characters.

5) File permissions issues
   chmod +x run_gateway.sh run_agent.sh
   Ensure ~/Library/LaunchAgents/*.plist are 644.

6) No rows in remote_ingest.db after push
   Confirm gateway reachable:
   curl -v -X POST http://127.0.0.1:8000/api/v1/nodes/status -H "Content-Type: application/json" -d '{"node_id":"test","payload":{"cpu":1}}'
   Check gateway logs: ./runtime/telemetry/logs/gateway.out.log

Useful one-liners
-----------------
1) Run single collect and push (from project root):
   TELEMETRY_PUSH_URL="http://127.0.0.1:8000/api/v1/nodes/status" TELEMETRY_PUSH_TOKEN="gemini123" python3 telemetry.py collect local-node --push

2) View last remote row quickly:
   sqlite3 ./runtime/telemetry/remote_ingest.db "SELECT id, node_id, timestamp FROM remote_telemetry ORDER BY id DESC LIMIT 1;"

3) Stop gateway and agent:
   pkill -f "uvicorn api_gateway:app" || true
   pkill -f "python3 telemetry.py scheduler" || pkill -f "telemetry.py scheduler" || true

Maintenance
-----------
1) Rotate logs: logs are rotated for agent.log (1MB, 3 backups). Gateway logs are stdout files; rotate via logrotate or manual scripts.
2) Backups: copy ./runtime/telemetry/*.db to a safe location regularly.
3) To package project:
   cd /Users/bretbarnard/Projects/gemini-mvp
   DATE=$(date +%Y%m%d); zip -r "gemini_controlplane_${DATE}.zip" . -x ".venv/*" "runtime/telemetry/logs/*"

Contact
-------
For operational help, run:
   python3 certify.py health
