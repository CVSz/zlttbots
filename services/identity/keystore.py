from __future__ import annotations

import os
import time
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROTATE_INTERVAL = int(os.getenv("KEY_ROTATE_SEC", "86400"))
DEFAULT_KEY_PATH = Path(os.getenv("AGENT_KEY_PATH", "/data/agent_ed25519.pem"))


class KeyStore:
    def __init__(self, key_path: Path | None = None) -> None:
        self.key_path = key_path or DEFAULT_KEY_PATH
        self.key = self._load_or_create(self.key_path)
        self.last_rotate = time.time()

    def _load_or_create(self, target: Path) -> Ed25519PrivateKey:
        if target.exists():
            return serialization.load_pem_private_key(target.read_bytes(), password=None)
        key = Ed25519PrivateKey.generate()
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(pem)
        return key

    def get(self) -> Ed25519PrivateKey:
        if time.time() - self.last_rotate > ROTATE_INTERVAL:
            self.key = Ed25519PrivateKey.generate()
            self.last_rotate = time.time()
        return self.key
