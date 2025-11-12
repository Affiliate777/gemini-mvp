import json
from pathlib import Path

def write_json_summary(results, path: Path):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    return path
