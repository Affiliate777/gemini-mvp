"""
storage.py
Ledger and storage helpers for Gemini MVP.

Responsibilities:
- Load config.json (with defaults)
- Simple tx pool helper (in-memory for this MVP)
- Build block from txs (uses merkle.merkle_root)
- Sign block header using crypto.sign_message
- Append block (JSON line) to ledger.jsonl
- Emit per-file proof JSON into proofs_dir (proof includes merkle branch etc.)
- Read / inspect ledger

Note: This is a minimalist, single-node ledger helper for the MVP.
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any

import merkle
import crypto

DEFAULT_CONFIG = {
    "ledger_path": os.path.expanduser("~/Library/Application Support/gemini-ledger/ledger.jsonl"),
    "proofs_dir": os.path.expanduser("~/Library/Application Support/gemini-ledger/proofs"),
    "batch_time_ms": 1000,
    "batch_count": 200,
    "private_key_path": os.path.expanduser("~/.ssh/gemini/gemini_ed25519")
}

_config = None

def load_config(path: str = None) -> Dict[str, Any]:
    global _config
    if _config:
        return _config
    cfg_path = Path(path) if path else Path(__file__).parent / "config.json"
    if cfg_path.exists():
        raw = json.loads(cfg_path.read_text())
        # expand ~ if present
        for k,v in raw.items():
            if isinstance(v, str) and v.startswith("~"):
                raw[k] = os.path.expanduser(v)
        cfg = {**DEFAULT_CONFIG, **raw}
    else:
        cfg = DEFAULT_CONFIG.copy()
    # ensure directories exist
    Path(cfg["ledger_path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg["proofs_dir"]).mkdir(parents=True, exist_ok=True)
    _config = cfg
    return _config

# Simple in-memory txpool for MVP
_txpool: List[Dict] = []

def add_tx(file_hash: str, meta: Dict = None, sender_did: str | None = None) -> Dict:
    """Add a tx to the in-memory pool and return tx object."""
    tx = {
        "file_hash": file_hash,
        "meta": meta or {},
        "sender_did": sender_did or f"did:gem:{crypto.pubkey_hex()}",
        "ts": int(time.time())
    }
    _txpool.append(tx)
    return tx

def peek_txpool() -> List[Dict]:
    return _txpool[:]

def clear_txpool():
    _txpool.clear()

# Ledger helpers
def _read_ledger(ledger_path: str) -> List[Dict]:
    ledger = []
    p = Path(ledger_path)
    if not p.exists():
        return ledger
    with p.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ledger.append(json.loads(line))
            except Exception:
                # skip corrupt lines
                continue
    return ledger

def last_block_info(ledger_path: str) -> Dict:
    ledger = _read_ledger(ledger_path)
    if not ledger:
        return {"index": -1, "hash": None}
    last = ledger[-1]
    return {"index": last["header"]["index"], "hash": last.get("block_hash")}

def _compute_block_hash(header: Dict) -> str:
    # Simple block hash = sha256 of canonical JSON header bytes
    import hashlib
    h = hashlib.sha256(json.dumps(header, sort_keys=True).encode()).hexdigest()
    return h

def create_block_and_append(cfg: Dict, txs: List[Dict]) -> Dict:
    """
    Build a Merkle root from txs, create a block header, sign it, and append to ledger.jsonl.
    Returns the full block dict (header, signature, txs, block_hash).
    """
    ledger_path = cfg["ledger_path"]
    ledger_last = last_block_info(ledger_path)
    index = ledger_last["index"] + 1
    # Leaves are file_hashes (hex)
    leaves = [t["file_hash"] for t in txs]
    if not leaves:
        raise ValueError("no txs to create block")
    root = merkle.merkle_root(leaves)
    header = {
        "index": index,
        "prev_hash": ledger_last["hash"],
        "merkle_root": root,
        "ts": int(time.time()),
        "signer_did": f"did:gem:{crypto.pubkey_hex(cfg.get('private_key_path'))}"
    }
    # sign header bytes
    header_bytes = json.dumps(header, sort_keys=True).encode()
    signature_hex = crypto.sign_message(header_bytes, cfg.get("private_key_path"))
    block_hash = _compute_block_hash(header)
    block = {
        "header": header,
        "block_signature": signature_hex,
        "block_hash": block_hash,
        "txs": txs
    }
    # append to ledger file (JSON Lines)
    with open(ledger_path, "a") as f:
        f.write(json.dumps(block) + "\n")
    # emit per-file proof files
    proofs_dir = Path(cfg["proofs_dir"])
    for tx_index, tx in enumerate(txs):
        proof = {
            "file_hash": tx["file_hash"],
            "tx": {"sender_did": tx["sender_did"], "tx_ts": tx["ts"], "tx_index": tx_index},
            "merkle_branch": merkle.get_proof(leaves, tx_index)["branch"],
            "positions": merkle.get_proof(leaves, tx_index)["positions"],
            "block_header": header,
            "block_signature": signature_hex,
            "block_index": index
        }
        # save proof next to file in proofs_dir using file_hash as filename
        proof_path = proofs_dir / f"{tx['file_hash']}.proof.json"
        with proof_path.open("w") as pf:
            json.dump(proof, pf)
    return block

def read_ledger(cfg: Dict) -> List[Dict]:
    return _read_ledger(cfg["ledger_path"])

# CLI test helper
if __name__ == "__main__":
    import argparse, hashlib
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true", help="create a sample block and append to ledger")
    args = p.parse_args()
    cfg = load_config()
    if args.test:
        # create a few sample txs based on random data
        sample_texts = ["alpha", "bravo", "charlie", "delta"]
        sample_txs = []
        for s in sample_texts:
            h = hashlib.sha256(s.encode()).hexdigest()
            sample_txs.append({"file_hash": h, "meta": {"sample": s}, "sender_did": f"did:gem:{crypto.pubkey_hex()}", "ts": int(time.time())})
        block = create_block_and_append(cfg, sample_txs)
        print("Appended block index:", block["header"]["index"])
        print("Block merkle_root:", block["header"]["merkle_root"])
        print("Ledger path:", cfg["ledger_path"])
