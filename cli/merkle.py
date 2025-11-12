"""
merkle.py
Tiny Merkle tree helpers for the Gemini MVP.

- Leaves: list of hex SHA256 strings (lowercase, no 0x).
- merkle_root(leaves) -> hex root
- get_proof(leaves, index) -> { "branch": [hexSibling...], "positions": ["left"|"right"...], "leaf": leaf_hex }
- verify_proof(leaf_hex, proof, root_hex) -> bool

Note: If odd number of nodes at a level, the last node is duplicated (classic simple Merkle).
No external deps.
"""
import hashlib
import json
from typing import List, Tuple, Dict

def _h_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def _hex_to_bytes(h: str) -> bytes:
    return bytes.fromhex(h)

def hash_pair_hex(left_hex: str, right_hex: str) -> str:
    """Hash two child hex strings and return hex digest."""
    lb = _hex_to_bytes(left_hex)
    rb = _hex_to_bytes(right_hex)
    return _h_bytes(lb + rb)

def merkle_root(leaves: List[str]) -> str:
    """Compute merkle root from list of leaf hex hashes. Returns hex root."""
    if not leaves:
        return _h_bytes(b'')  # define empty root as hash of empty bytes
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(hash_pair_hex(level[i], level[i+1]))
        level = nxt
    return level[0]

def _build_tree_levels(leaves: List[str]) -> List[List[str]]:
    """Return list of levels from leaves up; levels[0] == leaves, last == root-list-of-one."""
    if not leaves:
        return [[_h_bytes(b'')]]
    levels = [leaves[:]]
    level = leaves[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        nxt = []
        for i in range(0, len(level), 2):
            nxt.append(hash_pair_hex(level[i], level[i+1]))
        levels.append(nxt)
        level = nxt
    return levels

def get_proof(leaves: List[str], index: int) -> Dict:
    """
    Build Merkle inclusion proof for leaf at index.
    Returns:
      {
        "leaf": leaf_hex,
        "branch": [sibling_hex, ...],         # from leaf level upward
        "positions": ["left" or "right", ...] # position of sibling relative to current node
      }
    """
    if index < 0 or index >= len(leaves):
        raise IndexError("leaf index out of range")
    if not leaves:
        raise ValueError("no leaves")
    levels = _build_tree_levels(leaves)
    branch = []
    positions = []
    idx = index
    for level in levels[:-1]:  # skip the root level
        # ensure even by duplication
        l = level[:]
        if len(l) % 2 == 1:
            l.append(l[-1])
        sibling_index = idx ^ 1  # idx xor 1 gives sibling
        sibling_hash = l[sibling_index]
        # if idx is even, current is left, sibling is right
        if idx % 2 == 0:
            positions.append("right")
        else:
            positions.append("left")
        branch.append(sibling_hash)
        idx = idx // 2  # parent index in next level
    return {"leaf": leaves[index], "branch": branch, "positions": positions}

def verify_proof(leaf_hex: str, proof: Dict, root_hex: str) -> bool:
    """
    Verify inclusion proof.
    proof: { "leaf": leaf_hex, "branch": [sibling_hex...], "positions": ["left"|"right"...] }
    """
    try:
        cur = leaf_hex
        branch = proof.get("branch", [])
        positions = proof.get("positions", [])
        if len(branch) != len(positions):
            return False
        for sib, pos in zip(branch, positions):
            if pos == "left":
                # sibling is left, so hash(sibling || cur)
                cur = hash_pair_hex(sib, cur)
            elif pos == "right":
                # sibling is right, so hash(cur || sibling)
                cur = hash_pair_hex(cur, sib)
            else:
                return False
        return cur == root_hex
    except Exception:
        return False

# CLI test convenience
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true", help="run quick self-test")
    args = p.parse_args()
    if args.test:
        # sample leaves (sha256 of strings)
        leaves = [hashlib.sha256(x.encode()).hexdigest() for x in ["a","b","c","d","e"]]
        print("Leaves:", leaves)
        root = merkle_root(leaves)
        print("Root:", root)
        idx = 2
        proof = get_proof(leaves, idx)
        print("Proof for index", idx, json.dumps(proof, indent=2))
        print("Verify:", verify_proof(proof["leaf"], proof, root))
