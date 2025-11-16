import hashlib
from pathlib import Path
import json
from datetime import datetime

def _sha256_of_file(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def create_audit_entry(file_path: Path, certifier: str = None, register_local: bool = True):
    file_path = Path(file_path)
    sha = _sha256_of_file(file_path)
    entry = {
        "project_id": "CERT-001",
        "file": str(file_path),
        "sha256": sha,
        "certifier": certifier,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    if register_local:
        ledger_dir = Path("certify/ledger")
        ledger_dir.mkdir(parents=True, exist_ok=True)
        ledger_file = ledger_dir / "ledger.jsonl"
        with open(ledger_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    return entry
