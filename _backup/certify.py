"""
certify.py

Gemini Control-Plane CLI wrapper.
Connects to telemetry.py and exposes simple commands:

    python3 certify.py collect
    python3 certify.py show
    python3 certify.py scheduler
"""

import typer
import telemetry as t

app = typer.Typer(help="Gemini Control-Plane CLI")

@app.command()
def collect(node_id: str = "local-node"):
    """Collect a single telemetry snapshot."""
    payload = t.collect_system_metrics()
    t.push_telemetry(node_id, payload)
    typer.echo(f"[certify] collected telemetry for '{node_id}' at {payload.get('timestamp')}")

@app.command()
def show(limit: int = 20):
    """Display recent telemetry records."""
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
def scheduler(node_id: str = "local-node", interval: int = 30):
    """Continuously collect telemetry on an interval (Ctrl-C to stop)."""
    try:
        typer.echo(f"[certify] scheduler started for '{node_id}' every {interval}s (Ctrl-C to stop)")
        while True:
            payload = t.collect_system_metrics()
            t.push_telemetry(node_id, payload)
            typer.echo(f"[certify] collected telemetry at {payload.get('timestamp')}")
            t.time.sleep(interval)
    except KeyboardInterrupt:
        typer.echo("[certify] scheduler stopped.")

if __name__ == "__main__":
    app()
