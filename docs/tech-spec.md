# Gemini MVP Technical Specification

## 1. Architecture Overview

### 1.1 System Description
Gemini MVP is a **local-first blockchain certification engine**.  
It enables users to cryptographically certify files on their personal machine — without depending on remote nodes or cloud infrastructure.

The system creates a local, append-only **ledger** where each block records:
- A batch of file hashes (transactions),
- A Merkle root of those hashes,
- A timestamp,
- A digital signature proving authorship.

Each certified file generates a `.proof.json` receipt containing all necessary information to independently verify authenticity.

---

### 1.2 Core Components

| Component | Description |
|------------|-------------|
| **CLI Tools (`cli/`)** | Command-line utilities to certify (`certify.py`), verify (`verify.py`), and run the daemon. |
| **Crypto Module (`crypto.py`)** | Handles key management and digital signatures using Ed25519. |
| **Merkle Module (`merkle.py`)** | Builds and verifies Merkle trees for proof-of-inclusion validation. |
| **Storage Module (`storage.py`)** | Manages ledger persistence (JSON Lines file), block creation, and chaining. |
| **Daemon (`daemon.py`)** | Background watcher that monitors the ~/Certify folder and auto-certifies files. |

---

### 1.3 Ledger Layout
The ledger is stored at:
~/Library/Application Support/gemini-ledger/ledger.jsonl

Each **line** represents a block, stored as a JSON object:
{
  "header": {
    "index": 42,
    "prev_hash": "abcdef...",
    "merkle_root": "123456...",
    "ts": 1761510706,
    "signer_did": "did:gem:0983b71de486fca..."
  },
  "block_signature": "ed25519hex...",
  "txs": [ { "file_hash": "sha256...", "meta": { "filename": "report.pdf" } } ]
}

This structure supports **append-only immutability** and **local verification**.

---

### 1.4 Design Principles
- **Local-first**: No external dependencies for certification or verification.
- **Deterministic hashing**: Every file yields a single SHA-256 hash.
- **Compact storage**: Ledger entries use line-delimited JSON for easy streaming.
- **Offline verifiability**: Proofs are portable and can be verified without internet access.
- **Extensibility**: Future anchors (e.g., Hedera or Polygon) can be integrated via API.

## 2. Data Models

### 2.1 Transaction
Represents a single file fingerprint entry within a block.

Example:
{
  "file_hash": "6e71c5ced89ce7020e5cc3ff8ad2ceab6596289e1fca6c15fab47588bb66bc89",
  "meta": { "filename": "sample.txt" },
  "sender_did": "did:gem:0983b71de486fca023c014f458ca21c42723a3e603aafbb2bdc31b9dcbdab197",
  "ts": 1761510706
}

### 2.2 Block Header and Block
{
  "header": {
    "index": 3,
    "prev_hash": "8f6326ba12f82d4667811e1634f2550a55c8a55957ae190bc67544f65e9d35cf",
    "merkle_root": "70e0dc040cbbcba34f6319cba171129e617e590170608439f78a0ea0d0fd108d",
    "ts": 1761510706,
    "signer_did": "did:gem:0983b71de486fca..."
  },
  "block_signature": "af3dd7ae2b7395e0f7330ead1c746eca1bdc7017...",
  "block_hash": "121de750645ef05484229d3e5dd34c6aa4b0e1c545ff3057948bf7cbefd860ba",
  "txs": [ { "file_hash": "sha256..." } ]
}

### 2.3 Proof Object
Each certified file generates <file_hash>.proof.json.
{
  "file_hash": "6e71c5ced89ce7020e5cc3ff8ad2ceab6596289e1fca6c15fab47588bb66bc89",
  "merkle_branch": ["b9dd960c...", "f144a690..."],
  "positions": ["right", "right"],
  "block_header": { "index": 3, "ts": 1761510706 },
  "block_signature": "af3dd7ae2b7...",
  "block_index": 3,
  "anchor": null
}

### 2.4 Canonicalization
All JSON used for signatures or hashing is serialized with sorted keys (json.dumps(obj, sort_keys=True)), UTF-8 encoded, and hashed with SHA-256.


## 3. Flows

### 3.1 Certify Flow (Manual)
1. User executes `python cli/certify.py <file>`.
2. The CLI:
   - Computes `file_hash = SHA256(file_bytes)`.
   - Builds a transaction: `{ file_hash, meta, ts, sender_did }`.
   - Calls storage functions to create a new block containing that transaction.
   - Computes Merkle root, signs header, writes to `ledger.jsonl`.
   - Emits `<file_hash>.proof.json` under the proofs directory.
3. Console output confirms certification and block index.

### 3.2 Verify Flow (Offline)
1. User receives a file and its `.proof.json`.
2. Runs `python cli/verify.py <file> <proof>`.
3. The verifier:
   - Recomputes file hash.
   - Verifies Merkle proof inclusion.
   - Checks digital signature of the block header.
   - Returns VERIFIED ✅ or NOT VERIFIED ❌.

### 3.3 Daemon Flow (Automatic)
1. `daemon.py` monitors `~/Certify` for file creation/modification events.
2. On event:
   - Waits briefly to ensure file write completion.
   - Certifies the file using the same logic as manual flow.
   - Logs `[certify] path -> hash | block <index>`.
3. Ideal for background certification of working directories.

### 3.4 Dispatch Flow (Optional / Future)
1. When sending a file, the user packages:
   - The file,
   - Its `.proof.json`,
   - Optionally, a metadata envelope (recipient DID, permissions).
2. Recipient can verify provenance using `verify.py`.
3. Later iterations may write dispatch tx records back to the ledger to track custody and access.

### 3.5 Batch Flow (Planned)
- Instead of one block per file, accumulate transactions in memory:
  - Trigger block creation when batch count or time threshold is met.
  - Compute one Merkle tree for the batch.
  - Emit individual proofs for each tx.
- Improves performance and reduces ledger size for large-scale use.



## 4. Security & Integrity

### 4.1 Key Management
- Each Gemini instance generates a unique Ed25519 keypair on first run:
  - Stored under `~/.ssh/gemini/gemini_ed25519` (private) and `.pub` (public).
  - The **public key hash** defines the local identity DID:  
    `did:gem:<sha256(pubkey)>`.
- Keys remain local to the user’s machine; no key material leaves disk.
- Future integrations may add:
  - macOS Keychain / Linux Gnome Keyring secure storage.
  - Hardware-backed signing (e.g., YubiKey, TPM, or Secure Enclave).

---

### 4.2 Digital Signatures
- Each block’s header is signed using **Ed25519** over canonical JSON bytes.
- Verifiers:
  - Load the public key from the `signer_did`.
  - Canonicalize the header with `json.dumps(header, sort_keys=True)`.
  - Validate using `nacl.signing.VerifyKey`.
- Any tampering in block header fields (index, prev_hash, merkle_root) invalidates the signature.

---

### 4.3 Hashing & Merkle Integrity
- File fingerprints are deterministic using SHA-256.
- Merkle trees ensure inclusion proof via leaf→root reconstruction.
- The Merkle root is stored in each block header for O(1) verification.
- All hashes are lowercase hex, with no `0x` prefix.
- Proof verification:
  - Starts with file hash as leaf.
  - Iteratively hashes with sibling nodes according to position (`left`/`right`).
  - Confirms resulting hash equals stored `merkle_root`.

---

### 4.4 Ledger Integrity
- `ledger.jsonl` is an **append-only** structure; each line is a signed block.
- Each block header includes `prev_hash` referencing its predecessor.
- Validation tools can traverse the ledger:
  - Verify each `prev_hash` chain continuity.
  - Check signature validity for every header.
- Any deletion or insertion immediately breaks the hash chain.

---

### 4.5 Threat Model

| Threat | Mitigation |
|--------|-------------|
| File tampering after certification | SHA-256 mismatch + proof verification failure |
| Forged proofs | Invalid signature on block header |
| Ledger modification | `prev_hash` chain break |
| Key compromise | Local OS permissions / planned vault integration |
| Proof replay attacks | Timestamp validation + future anchor timestamping |

---

### 4.6 Future Hardening
- **Anchoring:** periodically publish block headers or Merkle roots to a public chain (Hedera, Polygon, or Bitcoin).
- **Encrypted Proof Bundles:** package proof+file using recipient’s public key.
- **Multi-signature Certification:** require multiple co-signers for certain file classes.
- **Revocation Ledger:** add “revoked” txs for obsolete or replaced files.

---

### 4.7 Verification Guarantees
A successful verification means:
1. The file hash existed at the recorded timestamp (`ts`).
2. The certifying user possessed the signing key (non-repudiation).
3. The ledger’s block chain of custody is unbroken.
4. The signature and Merkle reconstruction both validate.

**Result:** Gemini MVP ensures verifiable authorship, time-sealed proof, and tamper-evident integrity — fully offline.

---
**End of Technical Specification**
