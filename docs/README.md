# Gemini MVP — Blockchain On Demand

## Overview
Gemini is a local-first blockchain-on-demand engine that certifies, signs, and verifies files instantly — without external servers. It lets any user produce verifiable proof of authorship and file integrity directly from their desktop.

## Key Concepts
Each certified file produces a `.proof.json` in:
~/Library/Application Support/gemini-ledger/proofs/
containing:
- File hash (SHA-256)
- Merkle branch & root
- Block header (index, prev hash, timestamp)
- Digital signature (Ed25519)
- Signer DID (derived from your public key)

Local ledger:
~/Library/Application Support/gemini-ledger/ledger.jsonl

Daemon:
The daemon watches ~/Certify and stamps files automatically.

## Dev quickstart
cd ~/Projects/gemini-mvp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Certify:
python cli/certify.py data/sample.txt

Verify:
HASH=$(shasum -a 256 data/sample.txt | awk '{print $1}')
python cli/verify.py data/sample.txt "$HOME/Library/Application Support/gemini-ledger/proofs/${HASH}.proof.json"

**Author:** Jake Barnard — Version 0.1 (MVP)
