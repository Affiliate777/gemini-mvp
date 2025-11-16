"""
api_gateway.py

FastAPI gateway: fleet status + UI (auto-refresh). Renders recent alerts from controller summary.
"""
from __future__ import annotations
import os, json, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse, HTMLResponse

app = FastAPI(title="Gemini Telemetry Gateway", version="0.6")
RUNTIME_DIR = Path("./runtime/telemetry").resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = RUNTIME_DIR / "remote_ingest.db"
SUMMARY = RUNTIME_DIR / "fleet_summary.json"

def _read_token_from_file() -> Optional[str]:
    p = Path.home() / ".gemini" / "telemetry_token"
    try:
        if p.exists():
            return p.read_text(encoding="utf8").strip()
    except Exception:
        return None
    return None

EXPECTED_TOKEN = os.getenv("TELEMETRY_API_TOKEN") or _read_token_from_file()

def _ensure_db():
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS remote_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            payload TEXT
        )
    """)
    con.commit()
    con.close()

_ensure_db()

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@app.post("/api/v1/nodes/status")
async def ingest_status(request: Request, authorization: Optional[str] = Header(None)):
    if EXPECTED_TOKEN:
        if not authorization:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != EXPECTED_TOKEN:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    node_id = body.get("node_id")
    payload = body.get("payload")
    if not node_id or payload is None:
        raise HTTPException(status_code=400, detail="Missing 'node_id' or 'payload' in body")
    ts = _now_iso()
    payload_json = json.dumps(payload, default=str)
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("INSERT INTO remote_telemetry (node_id, timestamp, payload) VALUES (?, ?, ?)",
                (node_id, ts, payload_json))
    con.commit()
    con.close()
    return {"status": "ok", "node_id": node_id, "timestamp": ts}

@app.get("/api/v1/fleet/status")
def fleet_status():
    if not DB_PATH.exists():
        return JSONResponse({"node_count": 0, "nodes": [], "alerts": [], "generated_at": _now_iso()})
    con = sqlite3.connect(str(DB_PATH))
    cur = con.cursor()
    cur.execute("""
        SELECT id, node_id, timestamp, payload
        FROM remote_telemetry
        WHERE id IN (SELECT MAX(id) FROM remote_telemetry GROUP BY node_id)
        ORDER BY node_id
    """)
    rows = cur.fetchall()
    con.close()
    nodes: List[Dict[str, Any]] = []
    for _id, node_id, ts, payload_text in rows:
        try:
            payload = json.loads(payload_text)
        except Exception:
            payload = {}
        nodes.append({
            "node_id": node_id,
            "last_timestamp": ts,
            "last_payload": {
                "cpu_percent": payload.get("cpu_percent"),
                "mem_percent": payload.get("mem_percent"),
                "site": payload.get("site"),
                "project": payload.get("project")
            }
        })
    # try to read controller summary for alerts
    alerts = []
    if SUMMARY.exists():
        try:
            summary = json.loads(SUMMARY.read_text(encoding="utf8"))
            alerts = summary.get("alerts", [])
        except Exception:
            alerts = []
    return {"node_count": len(nodes), "nodes": nodes, "alerts": alerts, "generated_at": _now_iso()}

@app.get("/fleet/ui", response_class=HTMLResponse)
def fleet_ui():
    refresh_seconds = 15
    # try to read the controller summary JSON (preferred)
    summary = {}
    if (RUNTIME_DIR / "fleet_summary.json").exists():
        try:
            summary = json.loads((RUNTIME_DIR / "fleet_summary.json").read_text(encoding="utf8"))
        except Exception:
            summary = {}
    # fallback: build node rows from DB directly
    nodes_html = ""
    for n in summary.get("nodes", []):
        pid = n.get("node_id","")
        ts = n.get("last_timestamp","")
        payload = n.get("last_payload",{})
        cpu = payload.get("cpu_percent","")
        mem = payload.get("mem_percent","")
        site = payload.get("site","")
        project = payload.get("project","")
        nodes_html += f"<tr><td>{pid}</td><td>{ts}</td><td>{cpu}</td><td>{mem}</td><td>{site}</td><td>{project}</td></tr>\\n"

    # render alerts (most recent first)
    alerts_html = ""
    for a in summary.get("alerts", []):
        level = a.get("level","")
        msg = a.get("message","")
        g = a.get("gateway","")
        last_ts = a.get("last_remote_ts","")
        gen = a.get("generated_at","")
        alerts_html += f"<tr><td>{gen}</td><td>{level}</td><td>{last_ts}</td><td>{msg}</td></tr>\\n"

    html = f\"\"\"<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta http-equiv="refresh" content="{refresh_seconds}"/>
  <title>Gemini Fleet Status</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 16px; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 1200px; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f4f4f4; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    caption {{ font-size: 1.05em; margin-bottom: 8px; }}
  </style>
</head>
<body>
  <h1>Gemini Fleet Status</h1>
  <table>
    <caption>Nodes (last seen)</caption>
    <thead><tr><th>node_id</th><th>last_timestamp</th><th>cpu%</th><th>mem%</th><th>site</th><th>project</th></tr></thead>
    <tbody>
      {nodes_html}
    </tbody>
  </table>

  <table>
    <caption>Recent Alerts (latest first)</caption>
    <thead><tr><th>generated_at</th><th>level</th><th>last_remote_ts</th><th>message</th></tr></thead>
    <tbody>
      {alerts_html}
    </tbody>
  </table>

  <p>Generated at {_now_iso()}</p>
</body>
</html>\"\"\"
    return HTMLResponse(content=html, status_code=200)

@app.get("/")
def root():
    return {"status": "ok", "version": "api_gateway v0.6"}
