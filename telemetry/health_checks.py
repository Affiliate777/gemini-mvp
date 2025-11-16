from datetime import datetime, timezone
import os
import shutil
import socket
import platform
import json

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def hostname():
    return socket.gethostname()

def python_version():
    return platform.python_version()

def disk_usage(path="."):
    """Return disk usage stats in bytes for the given path."""
    usage = shutil.disk_usage(path)
    return {"total": usage.total, "used": usage.used, "free": usage.free}

def load_average():
    """Return 1/5/15-min load average where available. On platforms without os.getloadavg, return None."""
    try:
        one, five, fifteen = os.getloadavg()
        return {"1m": one, "5m": five, "15m": fifteen}
    except (AttributeError, OSError):
        return None

def env_snapshot(keys=None):
    keys = keys or ["PATH", "HOME"]
    return {k: os.environ.get(k) for k in keys}

def health_payload(extra=None):
    """Assemble a health payload suitable for /health JSON responses."""
    payload = {
        "hostname": hostname(),
        "timestamp": now_iso(),
        "python_version": python_version(),
        "disk": disk_usage("."),
        "load": load_average(),
    }
    if extra:
        payload["extra"] = extra
    return payload

def write_heartbeat_file(path_dir="var"):
    """Write heartbeat JSON to var/heartbeat_<hostname>.json. Return the path written."""
    os.makedirs(path_dir, exist_ok=True)
    fname = f"heartbeat_{hostname()}.json"
    full = os.path.join(path_dir, fname)
    payload = health_payload()
    with open(full, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return full

