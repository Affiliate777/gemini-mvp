"""
certify.py

Gemini Control-Plane CLI wrapper with health check.
"""
from __future__ import annotations
import typer
import telemetry as t
import sqlite3
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

app = typer.Typer(help="Gemini Control-Plane CLI")

@app.command()
def collect(node_id: str = "local-node", push: bool = False):
    payload = t.collect_system_metrics()
    t.push_telemetry(node_id, payload, push=push)
    typer.echo(f"[certify] collected telemetry for '{node_id}' at {payload.get('timestamp')}")

@app.command()
def show(limit: int = 20):
    store = t.get_default_store()
    rows = store.fetch_recent(limit)
    if not rows:
        typer.echo("No telemetry records found.")
        raise typer.Exit()
    for r in rows:
        node = r.get("node_id")
        ts = r.get("timestamp")
        cpu = r.get("payload", {}).get("cpu_percent")
        mem = r.get("payload", {}).get("mem_percent")
        typer.echo(f"- {ts} | node={node} | cpu={cpu} | mem={mem}")

@app.command()
def scheduler(node_id: str = "local-node", interval: int = 30, push: bool = False):
    try:
        typer.echo(f"[certify] scheduler started for '{node_id}' every {interval}s (Ctrl-C to stop)")
        while True:
            payload = t.collect_system_metrics()
            t.push_telemetry(node_id, payload, push=push)
            typer.echo(f"[certify] collected telemetry at {payload.get('timestamp')}")
            t.time.sleep(interval)
    except KeyboardInterrupt:
        typer.echo("[certify] scheduler stopped.")

@app.command()
def health(gateway_url: str = "http://127.0.0.1:8000", timeout: int = 3):
    """
    Health check:
      - HTTP check (gateway root)
      - local DB sizes
      - last remote telemetry timestamp
    """
    typer.echo("Health check starting...")
    # HTTP check
    try:
        req = urllib.request.Request(gateway_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            typer.echo(f"Gateway: reachable (status {resp.getcode()}) at {gateway_url}")
    except urllib.error.HTTPError as e:
        typer.echo(f"Gateway: reachable (HTTP {e.code}) at {gateway_url}")
    except Exception as e:
        typer.echo(f"Gateway: unreachable ({e}) at {gateway_url}")

    # DB checks
    runtime = Path("./runtime/telemetry")
    local_db = runtime / "telemetry.db"
    remote_db = runtime / "remote_ingest.db"

    def db_info(p: Path):
        if p.exists():
            try:
                size = p.stat().st_size
            except Exception:
                size = None
            return size
        return None

    typer.echo(f"Local DB: {local_db} size={db_info(local_db)}")
    typer.echo(f"Remote DB: {remote_db} size={db_info(remote_db)}")

    # last remote timestamp
    if remote_db.exists():
        try:
            con = sqlite3.connect(str(remote_db))
            cur = con.cursor()
            cur.execute("SELECT timestamp, node_id FROM remote_telemetry ORDER BY id DESC LIMIT 1;")
            row = cur.fetchone()
            con.close()
            if row:
                typer.echo(f"Remote DB last row: node={row[1]} ts={row[0]}")
            else:
                typer.echo("Remote DB last row: none")
        except Exception as e:
            typer.echo(f"Remote DB query failed: {e}")
    else:
        typer.echo("Remote DB: not found")

if __name__ == "__main__":
    app()
