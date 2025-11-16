#!/usr/bin/env python3
"""
daemon.py
Simple folder-watcher daemon for Gemini MVP.

- Watches configured folder (default ~/Certify)
- On new/modified regular files, calls storage.add_tx(...) and storage.create_block_and_append(...)
- Ignores files ending with .proof.json, hidden files, and directories.
- Designed for MVP reliability: immediate single-tx blocks, safe write-back of proofs.

Run:
  source ~/Projects/gemini-mvp/venv/bin/activate
  python daemon.py

Terminate with Ctrl+C.
"""
import time
import os
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

import storage
import hashlib

# default watch folder
DEFAULT_WATCH_FOLDER = os.path.expanduser("~/Certify")

# file filters
IGNORED_SUFFIXES = [".proof.json", ".tmp", ".swp", ".DS_Store"]
IGNORED_PREFIXES = ["."]  # hidden files

def is_ignored(path: Path) -> bool:
    name = path.name
    if any(name.endswith(s) for s in IGNORED_SUFFIXES):
        return True
    if any(name.startswith(p) for p in IGNORED_PREFIXES):
        return True
    if path.is_dir():
        return True
    return False

def compute_sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

class CertifyHandler(FileSystemEventHandler):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg

    def _maybe_certify(self, src_path: str):
        p = Path(src_path)
        try:
            if not p.exists() or not p.is_file():
                return
            if is_ignored(p):
                return
            # compute hash
            fh = compute_sha256(p)
            # add tx and append single-tx block (MVP behaviour)
            tx = storage.add_tx(fh, meta={"filename": p.name}, sender_did=None)
            block = storage.create_block_and_append(self.cfg, [tx])
            print(f"[certify] {p} -> {fh} | block {block['header']['index']}")
        except Exception as e:
            print("[certify] error for", src_path, e)

    def on_created(self, event):
        if isinstance(event, FileCreatedEvent):
            # small delay to let file finish writing
            time.sleep(0.2)
            self._maybe_certify(event.src_path)

    def on_modified(self, event):
        if isinstance(event, FileModifiedEvent):
            # avoid double-work for some editors by small debounce
            time.sleep(0.2)
            self._maybe_certify(event.src_path)

def main():
    cfg = storage.load_config()
    watch_folder = os.environ.get("GEMINI_WATCH_FOLDER", DEFAULT_WATCH_FOLDER)
    watch_path = Path(watch_folder).expanduser()
    watch_path.mkdir(parents=True, exist_ok=True)
    print("Gemini daemon watching:", str(watch_path))
    event_handler = CertifyHandler(cfg)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping daemon...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
