"""Simple client heartbeat emitter (callable from devices)."""
import time, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import requests
SERVER = os.environ.get("GEMINI_SERVER", "http://127.0.0.1:8765/telemetry/heartbeat")
def send_heartbeat(device_id, interval=30):
    while True:
        payload = {'id': device_id, 'ts': int(time.time())}
        try:
            r = requests.post(SERVER, json=payload, timeout=3)
            print('heartbeat', r.status_code, r.text)
        except Exception as e:
            print('heartbeat failed', repr(e))
        time.sleep(interval)
if __name__ == '__main__':
    dev = os.environ.get('GEMINI_DEVICE_ID', 'dev-0001')
    interval = int(os.environ.get('GEMINI_HEARTBEAT_INTERVAL', '10'))
    send_heartbeat(dev, interval)
