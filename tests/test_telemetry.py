import os
import json
import socket
from telemetry.health_checks import health_payload, write_heartbeat_file, disk_usage

def test_health_payload_contains_keys():
    p = health_payload()
    assert "hostname" in p
    assert "timestamp" in p
    assert "python_version" in p
    assert "disk" in p

def test_disk_usage_returns_numbers():
    d = disk_usage(".")
    assert isinstance(d["total"], int)
    assert isinstance(d["free"], int)
    assert d["total"] >= d["free"]

def test_write_heartbeat_file_creates_file(tmp_path, monkeypatch):
    # Make hostname deterministic for filename
    monkeypatch.setenv("HOSTNAME", "testhost")
    # Also monkeypatch socket.gethostname just in case the code uses it
    monkeypatch.setattr(socket, "gethostname", lambda: "testhost")
    out = write_heartbeat_file(path_dir=str(tmp_path))
    assert os.path.exists(out)
    with open(out, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data.get("hostname") is not None
    assert data.get("timestamp") is not None

