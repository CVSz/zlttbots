from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

KEY_PATH = Path(os.getenv("AGENT_KEY_PATH", "/data/agent_ed25519.pem"))


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def load_or_create_key(key_path: Path | None = None) -> Ed25519PrivateKey:
    target = key_path or KEY_PATH
    if target.exists():
        return serialization.load_pem_private_key(target.read_bytes(), password=None)

    secret_key = Ed25519PrivateKey.generate()
    pem = secret_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(pem)
    return secret_key


def get_did(secret_key: Ed25519PrivateKey) -> str:
    public_key = secret_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return "did:zttato:" + _b64(hashlib.sha256(public_key).digest()[:20])


def export_public_key(secret_key: Ed25519PrivateKey) -> str:
    public_key = secret_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64(public_key)


def sign(secret_key: Ed25519PrivateKey, payload: dict[str, Any]) -> tuple[str, str]:
    message = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    signature = secret_key.sign(message)
    return _b64(message), _b64(signature)


def verify(public_key_bytes: bytes, message_b64: str, signature_b64: str) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(_b64decode(signature_b64), _b64decode(message_b64))
        return True
    except Exception:
        return False
