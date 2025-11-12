#!/usr/bin/env python3
"""
certify.py
Minimal CLI to certify files for the Gemini MVP.

Usage:
  python certify.py file1.pdf file2.docx

What it does:
- Compute SHA-256(file bytes)
- Create a tx via storage.add_tx(...)
- Immediately create a block for the tx (single-tx block) via storage.create_block_and_append(...)
- Output location of the generated proof JSON (in proofs_dir) and a one-line summary.

This keeps the flow simple for the first pass. Later we'll run an async batcher (daemon) that combines many txs.
"""
import sys
import os
import hashlib
from pathlib import Path

import storage

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def certify_files(file_paths):
    cfg = storage.load_config()
    results = []
    for p in file_paths:
        path = Path(p).expanduser()
        if not path.exists() or not path.is_file():
            print(f"SKIP (not a file): {p}")
            continue
        file_hash = sha256_file(path)
        # create tx
        tx = storage.add_tx(file_hash, meta={"filename": path.name}, sender_did=None)
        # For this MVP we immediately create a block with only this tx
        block = storage.create_block_and_append(cfg, [tx])
        # proof path is stored as proofs_dir/<file_hash>.proof.json
        proof_path = Path(cfg["proofs_dir"]) / f"{file_hash}.proof.json"
        results.append({"file": str(path), "file_hash": file_hash, "proof": str(proof_path), "block_index": block["header"]["index"]})
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python certify.py <file1> [file2 ...]")
        sys.exit(1)
    files = sys.argv[1:]
    res = certify_files(files)
    for r in res:
        print(f"CERTIFIED {r['file']} -> hash {r['file_hash']}  proof: {r['proof']}  block: {r['block_index']}")

if __name__ == "__main__":
    main()
