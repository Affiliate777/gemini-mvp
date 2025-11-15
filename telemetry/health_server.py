import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import argparse
from telemetry.health_checks import health_payload, write_heartbeat_file

class HealthHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            payload = health_payload()
            self._send_json(200, payload)
        elif self.path == "/heartbeat-write":
            path = write_heartbeat_file()
            self._send_json(200, {"written": path})
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, format, *args):
        # Silence noisy default HTTPServer logging
        return

def run_server(host="0.0.0.0", port=8000):
    server = HTTPServer((host, port), HealthHandler)
    print(f"Telemetry health server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Server stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run telemetry health HTTP server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)
