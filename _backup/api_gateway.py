"""
api_gateway.py

FastAPI gateway for telemetry ingestion, fleet status and simple UI.
"""
from __future__ import annotations
import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse, HTMLResponse

app = FastAPI(title="Gemini Telemetry Gateway", version="0.3")
RUNTIME_DIR = Path("./runtime/telemetry").resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = RUNTIME_DIR / "remote_ingest.db"

EXPECTED_TOKEN = os.getenv("TELEMETRY_API_TOKEN")

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
        return JSONResponse({"node_count": 0, "nodes": [], "generated_at": _now_iso()})
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
        cpu = payload.get("cpu_percent")
        mem = payload.get("mem_percent")
        summary = {"cpu_percent": cpu, "mem_percent": mem}
        nodes.append({"node_id": node_id, "last_timestamp": ts, "last_payload": summary})
    return {"node_count": len(nodes), "nodes": nodes, "generated_at": _now_iso()}

@app.get("/fleet/ui", response_class=HTMLResponse)
def fleet_ui():
    if not DB_PATH.exists():
        html = "<html><head><title>Fleet Status</title></head><body><h1>Fleet Status</h1><p>No data available</p></body></html>"
        return HTMLResponse(content=html, status_code=200)
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
    rows_html = []
    for _id, node_id, ts, payload_text in rows:
        try:
            payload = json.loads(payload_text)
        except Exception:
            payload = {}
        cpu = payload.get("cpu_percent", "")
        mem = payload.get("mem_percent", "")
        # safe-escape minimal
        node_html = f"<tr><td>{node_id}</td><td>{ts}</td><td>{cpu}</td><td>{mem}</td></tr>"
        rows_html.append(node_html)
    table = "\n".join(rows_html)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Gemini Fleet Status</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; padding: 16px; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 1000px; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f4f4f4; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    caption {{ font-size: 1.2em; margin-bottom: 8px; }}
  </style>
</head>
<body>
  <h1>Gemini Fleet Status</h1>
  <table>
    <caption>Nodes (last seen)</caption>
    <thead><tr><th>node_id</th><th>last_timestamp</th><th>cpu%</th><th>mem%</th></tr></thead>
    <tbody>
      {table}
    </tbody>
  </table>
  <p>Generated at {_now_iso()}</p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)

@app.get("/")
def root():
    return {"status": "ok", "version": "api_gateway v0.3"}
