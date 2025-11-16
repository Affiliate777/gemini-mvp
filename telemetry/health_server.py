import json
import argparse
import shlex
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from telemetry.health_checks import health_payload, write_heartbeat_file

REPO_ROOT = "/Users/bretbarnard/Projects/gemini-mvp"
APPLY_SCRIPT = f"{REPO_ROOT}/scripts/update-apply.sh"
ROLLBACK_SCRIPT = f"{REPO_ROOT}/scripts/update-rollback.sh"

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
            return

        if self.path == "/heartbeat-write":
            path = write_heartbeat_file()
            self._send_json(200, {"written": path})
            return

        self._send_json(404, {"error": "not found"})

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _run_cmd(self, args):
        """Run a command (list) and return rc, stdout, stderr."""
        try:
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
            return proc.returncode, proc.stdout, proc.stderr
        except Exception as exc:
            return 255, "", str(exc)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/update/apply":
            body = self._read_json_body()
            version = body.get("version")
            target = body.get("target", REPO_ROOT)
            if not version:
                self._send_json(400, {"error": "missing 'version' in request body"})
                return

            src_dir = f"{REPO_ROOT}/updates/{version}"
            # quick safety check: ensure update snapshot exists
            try:
                import os
                if not os.path.isdir(src_dir):
                    self._send_json(404, {"error": f"update snapshot not found: {src_dir}"})
                    return
            except Exception:
                pass

            args = [APPLY_SCRIPT, version, target]
            rc, out, err = self._run_cmd(args)
            self._send_json(200 if rc == 0 else 500, {"rc": rc, "stdout": out, "stderr": err})
            return

        if parsed.path == "/update/rollback":
            body = self._read_json_body()
            target = body.get("target", REPO_ROOT)
            args = [ROLLBACK_SCRIPT, target]
            rc, out, err = self._run_cmd(args)
            self._send_json(200 if rc == 0 else 500, {"rc": rc, "stdout": out, "stderr": err})
            return

        # Unknown POST path
        self._send_json(404, {"error": "not found"})

    def log_message(self, format, *args):
        # Silence default HTTPServer logging to keep logs clean
        return

def run_server(host="0.0.0.0", port=8000):
    server = HTTPServer((host, port), HealthHandler)
    print(f"Telemetry health server running on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    run_server(args.host, args.port)
