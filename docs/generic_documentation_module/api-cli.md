# API & CLI Reference — TEST_DOCUMENTATION_MODULE

> Real, runnable examples from Jake's local environment. Contains local paths and example hashes. Do not publish.

Quick orientation
- Repo root: ~/Projects/gemini-mvp
- Virtualenv: ~/Projects/gemini-mvp/venv (activate with `source venv/bin/activate`)
- Keys: ~/.ssh/gemini/gemini_ed25519
- Ledger: ~/Library/Application Support/gemini-ledger/ledger.jsonl
- Proofs dir: ~/Library/Application Support/gemini-ledger/proofs/

---

certify.py — Quick Reference (real)
Command:
python cli/certify.py ~/Projects/gemini-mvp/data/sample.txt

Expected output (example):
CERTIFIED $HOME/Projects/gemini-mvp/data/sample.txt -> hash <sha256> proof: $HOME/Library/Application Support/gemini-ledger/proofs/<sha256>.proof.json block: 1

verify.py — Quick Reference (real)
Command:
python cli/verify.py ~/Projects/gemini-mvp/data/sample.txt "$HOME/Library/Application Support/gemini-ledger/proofs/<sha256>.proof.json"

daemon.py — Quick Reference (real)
Start:
source ~/Projects/gemini-mvp/venv/bin/activate
python cli/daemon.py

Test:
echo "daemon test $(date)" > ~/Certify/test1.txt

Where to look:
- Ledger: ~/Library/Application Support/gemini-ledger/ledger.jsonl
- Proofs: ~/Library/Application Support/gemini-ledger/proofs/
- Key pair: ~/.ssh/gemini/gemini_ed25519
