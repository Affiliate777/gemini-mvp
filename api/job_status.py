from flask import Flask, jsonify
import json
from pathlib import Path
import os

app = Flask(__name__)
_JOB_FILE = Path("var") / "jobs.json"

def _read_jobs():
    try:
        return json.loads(_JOB_FILE.read_text())
    except Exception:
        return {}

@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    jobs = _read_jobs()
    entry = jobs.get(job_id)
    if not entry:
        return jsonify({"error": "job not found"}), 404
    return jsonify(entry)

if __name__ == "__main__":
    port = int(os.environ.get("JOB_STATUS_PORT", "8010"))
    app.run(host="127.0.0.1", port=port)
