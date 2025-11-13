"""
Mock server (robust): logs tracebacks and returns JSON 500 instead of crashing.
"""
import os, sys, json, signal, time, traceback, logging
# ensure repo root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

LOGFILE = os.path.join(ROOT, "server.out.log")
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
logging.getLogger().addHandler(console)

HOST = '127.0.0.1'
PORT = int(os.environ.get("GEMINI_PORT", "8765"))

class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        try:
            body = json.dumps(payload).encode()
        except Exception:
            body = json.dumps({"error":"encoding_error"}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            # client closed connection early
            pass

    def parse_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode() if length else ''
        try:
            return json.loads(body) if body else {}
        except Exception:
            return {}

    def safe_handle(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logging.error("Exception handling request: %s\n%s", e, tb)
            # also write to stdout for interactive debugging
            print("Exception handling request:", e, file=sys.stderr)
            print(tb, file=sys.stderr)
            # return a 500 with short message + full trace in log file
            self._send(500, {"error": "internal_server_error", "message": str(e)})
            return

    def do_GET(self):
        self.safe_handle(self._do_GET)

    def _do_GET(self):
        path = urlparse(self.path).path
        if path == '/registry/list':
            from registry import store
            items = store.list_devices()
            return self._send(200, {"devices": items})
        if path == '/telemetry/heartbeat':
            return self._send(200, {"status": "ok", "server_time": int(time.time())})
        return self._send(404, {"error":"not_found"})

    def do_POST(self):
        self.safe_handle(self._do_POST)

    def _do_POST(self):
        path = urlparse(self.path).path
        data = self.parse_json_body()

        if path == '/registry/add':
            from registry import store
            store.add_device(data)
            return self._send(201, {"result":"added"})

        if path == '/telemetry/heartbeat':
            device_id = data.get('id')
            ts = data.get('ts', int(time.time()))
            metadata = data.get('metadata', None)
            if not device_id:
                return self._send(400, {"error":"missing_device_id"})
            from registry import store
            store.update_last_seen(device_id, ts, extra_metadata=metadata)
            return self._send(200, {"result":"heartbeat_received", "id": device_id, "ts": ts})

        if path == '/update/push':
            return self._send(202, {"result":"update_received"})

        return self._send(404, {"error":"not_found"})

def run():
    server = HTTPServer((HOST, PORT), Handler)
    msg = f"Mock server running at http://{HOST}:{PORT} (logs -> {LOGFILE})"
    print(msg)
    logging.info(msg)

    def _sigterm(signum, frame):
        logging.info('Shutting down...')
        server.shutdown()

    signal.signal(signal.SIGTERM, _sigterm)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == '__main__':
    run()
