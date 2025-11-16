#!/usr/bin/env python3
"""
generate_public_docs.py
Reads docs/test_documentation_module/api-cli.md and writes a sanitized version
to docs/generic_documentation_module/api-cli.generated.md
Replacements:
 - /Users/<username>/...  -> $HOME/...
 - 64-hex sha256 strings   -> <sha256>
 - absolute proof paths    -> $HOME/.../proofs/<sha256>.proof.json
"""
import re
from pathlib import Path

SRC = Path("docs/test_documentation_module/api-cli.md")
DST = Path("docs/generic_documentation_module/api-cli.generated.md")

if not SRC.exists():
    print("Source test doc not found:", SRC)
    raise SystemExit(1)

text = SRC.read_text(encoding="utf-8")

# Replace /Users/<name> with $HOME
text = re.sub(r"/Users/[A-Za-z0-9._-]+", "$HOME", text)

# Replace 64-hex hashes with <sha256>
text = re.sub(r"\b([a-f0-9]{64})\b", "<sha256>", text)

# Replace explicit proof paths containing a hash with generic proof path
text = re.sub(r"\$HOME/Library/Application Support/gemini-ledger/proofs/\S+\.proof\.json",
              "$HOME/Library/Application Support/gemini-ledger/proofs/<sha256>.proof.json", text)

DST.write_text(text, encoding="utf-8")
print("Wrote sanitized doc to", DST)
