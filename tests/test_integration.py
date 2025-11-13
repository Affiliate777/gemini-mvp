import os
import time
import subprocess
import requests
import signal
import sys
from urllib.parse import urljoin

SERVER_PORT = int(os.environ.get("GEMINI_TEST_PORT", "8767"))
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
PYTHON = sys.executable

def start_server(env=None):
    env = env or os.environ.copy()
    env["GEMINI_PORT"] = str(SERVER_PORT)
    p = subprocess.Popen([PYTHON, "-u", "-m", "runtime.mock_server"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p

def wait_ready(url, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(urljoin(url, "/telemetry/heartbeat"), timeout=1.0)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(0.2)
    return False

def test_server_add_and_heartbeat():
    p = start_server()
    try:
        assert wait_ready(SERVER_URL), "server did not become ready"
        payload = {"id": "it-dev-0001", "node_type": "edge", "channel_version": "0.1.0", "metadata": {"env": "test"}}
        r = requests.post(urljoin(SERVER_URL, "/registry/add"), json=payload, timeout=3.0)
        assert r.status_code == 201, f"failed add: {r.status_code} {r.text}"
        hb = {"id": "it-dev-0001", "ts": int(time.time())}
        r2 = requests.post(urljoin(SERVER_URL, "/telemetry/heartbeat"), json=hb, timeout=3.0)
        assert r2.status_code == 200, f"heartbeat failed: {r2.status_code} {r2.text}"
        r3 = requests.get(urljoin(SERVER_URL, "/registry/list"), timeout=3.0)
        assert r3.status_code == 200
        data = r3.json()
        assert "devices" in data
        found = [d for d in data["devices"] if d.get("id") == "it-dev-0001"]
        assert len(found) == 1
        assert found[0].get("last_seen") is not None
    finally:
        try:
            p.send_signal(signal.SIGTERM)
            p.wait(timeout=3.0)
        except Exception:
            p.kill()
