from __future__ import annotations

import base64
from typing import Any

from kms_verify import verify



def apply_patch_request(patch_b64: str, sig_b64: str) -> dict[str, Any]:
    if not verify(patch_b64, sig_b64):
        return {"status": "invalid_signature"}

    patch_bytes = base64.b64decode(patch_b64)
    return {"status": "verified", "patch_size_bytes": len(patch_bytes)}
