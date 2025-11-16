#!/usr/bin/env python3
"""
verify.py
Offline verifier for Gemini MVP (fixed JSON scope bug).
"""

import sys
import json
import hashlib
from pathlib import Path
import merkle
import crypto

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def verify(file_path: str, proof_path: str) -> bool:
    fpath = Path(file_path).expanduser()
    ppath = Path(proof_path).expanduser()

    if not fpath.exists() or not fpath.is_file():
        print("ERROR: file not found:", fpath)
        return False
    if not ppath.exists() or not ppath.is_file():
        print("ERROR: proof not found:", ppath)
        return False

    file_hash = sha256_file(fpath)
    proof = json.loads(ppath.read_text())
    expected_hash = proof.get("file_hash")
    if file_hash != expected_hash:
        print("NOT VERIFIED: file hash mismatch")
        print("  computed:", file_hash)
        print("  proof   :", expected_hash)
        return False

    # verify Merkle inclusion
    leaf = proof.get("file_hash")
    branch = {
        "leaf": leaf,
        "branch": proof.get("merkle_branch", []),
        "positions": proof.get("positions", [])
    }
    root = proof["block_header"]["merkle_root"]
    if not merkle.verify_proof(leaf, branch, root):
        print("NOT VERIFIED: merkle inclusion failed")
        return False

    # verify block signature
    header = proof["block_header"]
    header_bytes = json.dumps(header, sort_keys=True).encode()
    sig = proof.get("block_signature")
    signer_pk = header.get("signer_did", "").split(":")[-1]
    if not sig or not signer_pk:
        print("NOT VERIFIED: missing signature or signer pubkey")
        return False
    if not crypto.verify_message(header_bytes, sig, signer_pk):
        print("NOT VERIFIED: block signature invalid")
        return False

    # all good
    print("VERIFIED ✅")
    print(f"  file_hash : {file_hash}")
    print(f"  block idx : {proof.get('block_index')}  merkle_root: {root}")
    print(f"  signer    : {header.get('signer_did')}")
    print(f"  ts        : {header.get('ts')}")
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python verify.py <file> <proof.json>")
        sys.exit(1)
    ok = verify(sys.argv[1], sys.argv[2])
    if not ok:
        sys.exit(2)

if __name__ == "__main__":
    main()
