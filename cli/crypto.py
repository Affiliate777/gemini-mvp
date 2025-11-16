"""
crypto.py
Minimal Ed25519 helpers for the Gemini MVP.

- Loads an OpenSSH Ed25519 private key (the one you created at ~/.ssh/gemini/gemini_ed25519)
  using cryptography, extracts raw private bytes, and wraps them in a PyNaCl SigningKey.
- Exposes sign(message_bytes) -> signature_hex
- Exposes verify(message_bytes, signature_hex, pubkey_hex) -> bool
- Exposes pubkey_hex() -> hex string of the node's public key

Dependencies:
  pip install pynacl cryptography
"""

import os
from pathlib import Path
import binascii

# PyNaCl for signing
import nacl.signing
import nacl.exceptions

# cryptography for loading OpenSSH private key
from cryptography.hazmat.primitives.serialization import load_ssh_private_key, Encoding, PrivateFormat, NoEncryption

DEFAULT_KEY_PATH = os.path.expanduser("~/.ssh/gemini/gemini_ed25519")

def load_signing_key(private_key_path: str = None, password: bytes | None = None) -> nacl.signing.SigningKey:
    """
    Load an Ed25519 private key from an OpenSSH-format key file and return a PyNaCl SigningKey.
    If the file doesn't exist, raises FileNotFoundError.
    """
    path = Path(private_key_path or DEFAULT_KEY_PATH).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Private key not found: {path}")

    with open(path, "rb") as f:
        key_data = f.read()

    # cryptography returns an Ed25519PrivateKey
    priv = load_ssh_private_key(key_data, password=password)
    # get raw private bytes (32 bytes seed)
    raw_priv = priv.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption()
    )
    # Wrap with PyNaCl SigningKey
    sk = nacl.signing.SigningKey(raw_priv)
    return sk

def sign_message(message: bytes, private_key_path: str = None) -> str:
    """
    Sign a message (bytes) and return signature as hex string.
    """
    sk = load_signing_key(private_key_path)
    signed = sk.sign(message)
    sig = signed.signature  # bytes
    return binascii.hexlify(sig).decode()

def verify_message(message: bytes, signature_hex: str, pubkey_hex: str) -> bool:
    """
    Verify signature_hex (hex) against message bytes and public key hex.
    Returns True if valid, False otherwise.
    """
    try:
        vk_bytes = binascii.unhexlify(pubkey_hex)
        vk = nacl.signing.VerifyKey(vk_bytes)
        sig_bytes = binascii.unhexlify(signature_hex)
        # Verify by concatenating signature + message as PyNaCl expects signed blob, or use verify() directly:
        vk.verify(message, sig_bytes)
        return True
    except (binascii.Error, nacl.exceptions.BadSignatureError, Exception):
        return False

def pubkey_hex(private_key_path: str = None) -> str:
    """
    Return the public key hex (64-char hex for 32 bytes).
    """
    sk = load_signing_key(private_key_path)
    vk = sk.verify_key
    return binascii.hexlify(vk.encode()).decode()

# quick CLI helper for manual testing
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--key", help="private key path (optional)")
    p.add_argument("--test", action="store_true", help="run quick sanity test")
    args = p.parse_args()
    if args.test:
        msg = b"gemini-test"
        print("Using key:", args.key or DEFAULT_KEY_PATH)
        sig = sign_message(msg, args.key)
        pk = pubkey_hex(args.key)
        print("pubkey:", pk)
        print("sig:", sig)
        print("verify ok?", verify_message(msg, sig, pk))
