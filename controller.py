#!/usr/bin/env python3
"""
controller.py

Builds fleet_summary.json combining latest node telemetry and recent alerts.
"""
from __future__ import annotations
import sqlite3, json, textwrap
from pathlib import Path
from datetime import datetime, timezone

RUNTIME = Path("./runtime/telemetry").resolve()
RUNTIME.mkdir(parents=True, exist_ok=True)
REMOTE_DB = RUNTIME / "remote_ingest.db"
ALERT_DB = RUNTIME / "alerts.db"
OUT = RUNTIME / "fleet_summary.json"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def fetch_nodes():
    nodes = []
    if not REMOTE_DB.exists():
        return nodes
    con = sqlite3.connect(str(REMOTE_DB))
    cur = con.cursor()
    # get latest row id per node
    cur.execute("""
        SELECT id, node_id, timestamp, payload
        FROM remote_telemetry
        WHERE id IN (SELECT MAX(id) FROM remote_telemetry GROUP BY node_id)
        ORDER BY node_id
    """)
    rows = cur.fetchall()
    con.close()
    for _id, node_id, ts, payload_text in rows:
        try:
            payload = json.loads(payload_text)
        except Exception:
            payload = {}
        nodes.append({
            "node_id": node_id,
            "last_timestamp": ts,
            "last_payload": payload
        })
    return nodes

def fetch_alerts(limit=50):
    alerts = []
    if not ALERT_DB.exists():
        return alerts
    con = sqlite3.connect(str(ALERT_DB))
    cur = con.cursor()
    cur.execute("SELECT id, level, message, gateway, last_remote_ts, generated_at FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    for _id, level, message, gateway, last_remote_ts, generated_at in rows:
        alerts.append({
            "id": _id,
            "level": level,
            "message": message,
            "gateway": gateway,
            "last_remote_ts": last_remote_ts,
            "generated_at": generated_at
        })
    return alerts

def build_summary():
    nodes = fetch_nodes()
    alerts = fetch_alerts(limit=50)
    summary = {
        "node_count": len(nodes),
        "nodes": nodes,
        "alerts": alerts,
        "generated_at": now_iso()
    }
    OUT.write_text(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    s = build_summary()
    print(f"nodes={s['node_count']} alerts={len(s['alerts'])} generated_at={s['generated_at']}")
