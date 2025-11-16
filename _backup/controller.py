"""
controller.py

Simple orchestrator: reads remote_ingest.db and writes fleet_summary.json

Usage:
  python3 controller.py   # writes runtime/telemetry/fleet_summary.json and prints a short summary
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

RUNTIME = Path("./runtime/telemetry").resolve()
DB = RUNTIME / "remote_ingest.db"
OUT = RUNTIME / "fleet_summary.json"

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def build_summary():
    if not DB.exists():
        summary = {"node_count": 0, "nodes": [], "generated_at": now_iso()}
        OUT.write_text(json.dumps(summary, indent=2))
        return summary
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    cur.execute("SELECT id, node_id, timestamp, payload FROM remote_telemetry WHERE id IN (SELECT MAX(id) FROM remote_telemetry GROUP BY node_id) ORDER BY node_id")
    rows = cur.fetchall()
    con.close()
    nodes = []
    for _id, node_id, ts, payload_text in rows:
        try:
            payload = json.loads(payload_text)
        except Exception:
            payload = {}
        nodes.append({"node_id": node_id, "last_timestamp": ts, "last_payload": payload})
    summary = {"node_count": len(nodes), "nodes": nodes, "generated_at": now_iso()}
    OUT.write_text(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    s = build_summary()
    print(f"nodes={s['node_count']} generated_at={s['generated_at']}")
