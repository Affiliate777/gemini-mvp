import argparse
from telemetry.health_checks import write_heartbeat_file
import sys

def run_once(path_dir="var", verbose=False):
    path = write_heartbeat_file(path_dir=path_dir)
    if verbose:
        print(f"Wrote heartbeat to {path}")
    return path

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="var", help="Directory to write heartbeat files")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    try:
        out = run_once(path_dir=args.dir, verbose=args.verbose)
        sys.exit(0)
    except Exception as exc:
        print("Agent failed:", exc, file=sys.stderr)
        sys.exit(2)
