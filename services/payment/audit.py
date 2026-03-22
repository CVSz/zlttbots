from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.getenv("PAYMENT_AUDIT_LOG", "/tmp/payment_audit.log"))



def log(event: str, data: dict[str, Any]) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "ts": int(time.time()),
                    "event": event,
                    "data": data,
                },
                sort_keys=True,
            )
            + "\n"
        )
