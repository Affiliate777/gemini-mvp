#!/usr/bin/env python3
"""
alert.py (local-only)

Writes alerts to:
 - runtime/telemetry/alerts.db (SQLite)
 - runtime/telemetry/alerts.jsonl  (append-only)
Also logs to runtime/telemetry/alerts.log for human inspection.

No webhooks. Dashboard will read the alerts DB/jsonl.
"""
from __future__ import annotations
import os, sys, json, sqlite3, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# runtime paths (project-local)
RUNTIME = Path("./runtime/telemetry").resolve()
RUNTIME.mkdir(parents=True, exist_ok=True)
ALERT_LOG = RUNTIME / "alerts.log"
ALERT_JSONL = RUNTIME / "alerts.jsonl"
ALERT_DB = RUNTIME / "alerts.db"
REMOTE_DB = RUNTIME / "remote_ingest.db"

# config from env
GATEWAY = os.getenv("TELEMETRY_PUSH_URL", "http://127.0.0.1:8000").rstrip("/") + "/"
TOKEN = os.getenv("TELEMETRY_API_TOKEN")
MAX_AGE_MIN = int(os.getenv("ALERT_MAX_AGE_MIN", "10"))

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def log(msg: str):
    line = f"{now_iso()} {msg}\n"
    with open(ALERT_LOG, "a", encoding="utf8") as fh:
        fh.write(line)
    print(line, end="")

def _ensure_db():
    con = sqlite3.connect(str(ALERT_DB))
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT,
            message TEXT,
            gateway TEXT,
            last_remote_ts TEXT,
            generated_at TEXT
        )
    """)
    con.commit()
    con.close()

def write_alert(level: str, message: str, last_remote_ts: Optional[str]):
    _ensure_db()
    ts = now_iso()
    payload = {
        "level": level,
        "message": message,
        "gateway": GATEWAY,
        "last_remote_ts": last_remote_ts,
        "generated_at": ts
    }
    # insert into sqlite
    con = sqlite3.connect(str(ALERT_DB))
    cur = con.cursor()
    cur.execute("INSERT INTO alerts (level, message, gateway, last_remote_ts, generated_at) VALUES (?, ?, ?, ?, ?)",
                (level, message, GATEWAY, last_remote_ts, ts))
    con.commit()
    con.close()
    # append to jsonl
    with open(ALERT_JSONL, "a", encoding="utf8") as fh:
        fh.write(json.dumps(payload, default=str) + "\n")
    log(f"[ALERT STORED] level={level} msg={message}")

def check_gateway() -> tuple[bool, Optional[int|str]]:
    try:
        req = urllib.request.Request(GATEWAY, method="GET")
        if TOKEN:
            req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, resp.getcode()
    except urllib.error.HTTPError as e:
        return True, getattr(e, "code", None)
    except Exception as e:
        return False, str(e)

def last_remote_timestamp() -> Optional[str]:
    if not REMOTE_DB.exists():
        return None
    try:
        con = sqlite3.connect(str(REMOTE_DB))
        cur = con.cursor()
        cur.execute("SELECT timestamp FROM remote_telemetry ORDER BY id DESC LIMIT 1;")
        r = cur.fetchone()
        con.close()
        return r[0] if r else None
    except Exception:
        return None

def parse_iso(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        try:
            from datetime import datetime as _dt
            return _dt.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z")
        except Exception:
            return None

def main():
    ok = True
    issues = []
    gw_ok, gw_info = check_gateway()
    if not gw_ok:
        msg = f"Gateway unreachable ({gw_info})"
        log("[ERROR] " + msg)
        issues.append(msg)
        ok = False
    else:
        log(f"[DEBUG] Gateway reachable (info={gw_info})")

    ts = last_remote_timestamp()
    if ts is None:
        msg = "No remote telemetry rows found"
        log("[WARN] " + msg)
        issues.append(msg)
        ok = False
    else:
        parsed = parse_iso(ts)
        if parsed is None:
            msg = f"Could not parse last timestamp: {ts}"
            log("[WARN] " + msg)
            issues.append(msg)
            ok = False
        else:
            age_min = (datetime.now(timezone.utc) - parsed).total_seconds() / 60.0
            if age_min > MAX_AGE_MIN:
                msg = f"Last remote telemetry is stale: {ts} ({age_min:.1f} minutes)"
                log("[WARN] " + msg)
                issues.append(msg)
                ok = False
            else:
                log(f"[INFO] Last remote telemetry OK: {ts} ({age_min:.1f} minutes)")

    if not ok:
        write_alert("ALERT", "; ".join(issues), ts)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
