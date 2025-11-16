"""
telemetry.py (logging-enabled)

Adds file logging with rotation:
logs path: ./runtime/telemetry/logs/agent.log
rotation: 1_000_000 bytes, 3 backups
"""
from __future__ import annotations
import os
import sys
import json
import time
import socket
import sqlite3
import platform
import urllib.request
import urllib.error
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

DEFAULT_DIR = Path("./runtime/telemetry").resolve()
DEFAULT_SQLITE = DEFAULT_DIR / "telemetry.db"
DEFAULT_JSONL = DEFAULT_DIR / "telemetry.jsonl"
LOG_DIR = DEFAULT_DIR / "logs"
LOG_FILE = LOG_DIR / "agent.log"

DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("telemetry")
if not logger.handlers:
    handler = RotatingFileHandler(str(LOG_FILE), maxBytes=1_000_000, backupCount=3, encoding="utf8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def collect_system_metrics() -> Dict[str, Any]:
    ts = _now_iso()
    hostname = socket.gethostname()
    plat = platform.platform()
    try:
        load = os.getloadavg() if hasattr(os, "getloadavg") else (0.0, 0.0, 0.0)
        cpu_count = os.cpu_count() or 1
        cpu_percent = round((load[0] / max(1, cpu_count)) * 100, 2)
    except Exception:
        cpu_percent = None
        cpu_count = os.cpu_count() or None

    mem_total = mem_used = mem_percent = None
    if os.path.exists("/proc/meminfo"):
        try:
            info = {}
            for ln in open("/proc/meminfo", "r", encoding="utf8"):
                if ":" in ln:
                    k, v = ln.split(":", 1)
                    info[k.strip()] = v.strip()
            if "MemTotal" in info and "MemAvailable" in info:
                total_kb = int(info["MemTotal"].split()[0])
                avail_kb = int(info["MemAvailable"].split()[0])
                mem_total = total_kb * 1024
                mem_used = mem_total - (avail_kb * 1024)
                mem_percent = round((mem_used / mem_total) * 100, 2) if mem_total else None
        except Exception:
            mem_total = mem_used = mem_percent = None

    try:
        st = os.statvfs("/")
        disk_total = st.f_frsize * st.f_blocks
        disk_free = st.f_frsize * st.f_bfree
        disk_used = disk_total - disk_free
        disk_percent = round((disk_used / disk_total) * 100, 2) if disk_total else None
    except Exception:
        disk_total = disk_used = disk_percent = None

    uptime_seconds = None
    if os.path.exists("/proc/uptime"):
        try:
            uptime_seconds = float(open("/proc/uptime", "r", encoding="utf8").read().split()[0])
        except Exception:
            uptime_seconds = None

    metrics = {
        "timestamp": ts,
        "hostname": hostname,
        "platform": plat,
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "mem_total": mem_total,
        "mem_used": mem_used,
        "mem_percent": mem_percent,
        "disk_total": disk_total,
        "disk_used": disk_used,
        "disk_percent": disk_percent,
        "uptime_seconds": uptime_seconds,
    }
    return metrics

class TelemetryStore:
    def __init__(self, sqlite_path: Optional[Path] = None, jsonl_path: Optional[Path] = None):
        self.sqlite_path = Path(sqlite_path or DEFAULT_SQLITE)
        self.jsonl_path = Path(jsonl_path or DEFAULT_JSONL)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_sqlite()

    def _ensure_sqlite(self):
        con = sqlite3.connect(str(self.sqlite_path))
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT,
                timestamp TEXT,
                payload TEXT
            )
        """)
        con.commit(); con.close()

    def insert(self, node_id: str, payload: Dict[str, Any]):
        ts = payload.get("timestamp") or _now_iso()
        payload_json = json.dumps(payload, default=str)
        con = sqlite3.connect(str(self.sqlite_path))
        cur = con.cursor()
        cur.execute("INSERT INTO telemetry (node_id, timestamp, payload) VALUES (?, ?, ?)",
                    (node_id, ts, payload_json))
        con.commit(); con.close()
        with open(self.jsonl_path, "a", encoding="utf8") as fh:
            fh.write(json.dumps({"node_id": node_id, "timestamp": ts, "payload": payload}, default=str) + "\n")
        logger.info("local insert node=%s ts=%s", node_id, ts)

    def fetch_recent(self, limit: int = 20) -> list[Dict[str, Any]]:
        con = sqlite3.connect(str(self.sqlite_path))
        cur = con.cursor()
        cur.execute("SELECT node_id, timestamp, payload FROM telemetry ORDER BY id DESC LIMIT ?", (limit,))
        rows = cur.fetchall(); con.close()
        out = []
        for node_id, ts, payload_json in rows:
            try:
                payload = json.loads(payload_json)
            except Exception:
                payload = {"raw": payload_json}
            out.append({"node_id": node_id, "timestamp": ts, "payload": payload})
        return out

_default_store: Optional[TelemetryStore] = None
def get_default_store() -> TelemetryStore:
    global _default_store
    if _default_store is None:
        _default_store = TelemetryStore()
    return _default_store

def _http_post(url: str, data: bytes, headers: Optional[Dict[str, str]] = None, timeout: int = 5) -> tuple[int, str]:
    headers = headers or {}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf8", errors="replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception as e:
        raise

def push_remote(node_id: str, payload: Dict[str, Any], url: Optional[str] = None, token: Optional[str] = None) -> bool:
    target = url or os.getenv("TELEMETRY_PUSH_URL") or "http://127.0.0.1:8000/api/v1/nodes/status"
    auth_token = token or os.getenv("TELEMETRY_PUSH_TOKEN")
    body = json.dumps({"node_id": node_id, "payload": payload}, default=str).encode("utf8")
    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    backoff = 1.0
    for attempt in range(3):
        try:
            code, resp = _http_post(target, body, headers=headers, timeout=5)
            msg = f"[telemetry->remote] success code={code}"
            print(msg)
            logger.info(msg + " node=%s", node_id)
            return True
        except Exception as e:
            msg = f"[telemetry->remote] attempt {attempt+1} failed: {e}"
            print(msg)
            logger.warning(msg + " node=%s", node_id)
            time.sleep(backoff)
            backoff *= 2.0
    msg = "[telemetry->remote] failed after retries"
    print(msg)
    logger.error(msg + " node=%s", node_id)
    return False

def push_telemetry(node_id: str, payload: Dict[str, Any], store: Optional[TelemetryStore] = None, push: bool = False):
    st = store or get_default_store()
    try:
        st.insert(node_id, payload)
    except Exception as e:
        err = f"[telemetry] local insert failed: {e}"
        print(err)
        logger.exception(err)
    if push:
        push_remote(node_id, payload)

def _print_help():
    print("telemetry.py - local telemetry agent with optional remote push")
    print("Usage:")
    print("  python3 telemetry.py collect <node_id> [--push]")
    print("  python3 telemetry.py show [limit]")
    print("  python3 telemetry.py scheduler <node_id> <interval_seconds> [--push]")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        _print_help(); sys.exit(0)
    cmd = args[0]
    if cmd == "collect":
        node_id = args[1] if len(args) > 1 and not args[1].startswith("--") else "local-node"
        push_flag = "--push" in args
        payload = collect_system_metrics()
        push_telemetry(node_id, payload, push=push_flag)
        print(f"[telemetry] collected for '{node_id}' at {payload.get('timestamp')}")
    elif cmd == "show":
        limit = int(args[1]) if len(args) > 1 else 20
        st = get_default_store()
        for r in st.fetch_recent(limit=limit):
            node = r.get("node_id"); ts = r.get("timestamp")
            cpu = r.get("payload", {}).get("cpu_percent"); mem = r.get("payload", {}).get("mem_percent")
            print(f"- {ts} | node={node} | cpu={cpu} | mem={mem}")
    elif cmd == "scheduler":
        node_id = args[1] if len(args) > 1 and not args[1].startswith("--") else "local-node"
        interval = int(args[2]) if len(args) > 2 and not args[2].startswith("--") else 30
        push_flag = "--push" in args
        try:
            print(f"[telemetry] scheduler running for '{node_id}' every {interval}s (Ctrl-C to stop)")
            while True:
                p = collect_system_metrics()
                push_telemetry(node_id, p, push=push_flag)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[telemetry] scheduler stopped")
    else:
        _print_help()
