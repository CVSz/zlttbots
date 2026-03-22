from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DEFAULT_KEY_PATH = Path("/models/agent_ed25519.pem")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def load_or_create_key(key_path: Path | None = None) -> Ed25519PrivateKey:
    target = key_path or DEFAULT_KEY_PATH
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
    return _b64(message), _b64(secret_key.sign(message))


def build_heartbeat_identity(key_path: Path | None = None) -> dict[str, str | Ed25519PrivateKey]:
    secret_key = load_or_create_key(key_path)
    did = get_did(secret_key)
    message_b64, signature_b64 = sign(secret_key, {"op": "heartbeat", "did": did})
    return {
        "secret_key": secret_key,
        "did": did,
        "message_b64": message_b64,
        "signature_b64": signature_b64,
        "public_key_b64": export_public_key(secret_key),
    }
