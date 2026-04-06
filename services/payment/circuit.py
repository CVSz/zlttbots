from __future__ import annotations

import time

FAILS = 0
OPEN = False
LAST_FAIL = 0.0
RESET_AFTER_SECONDS = 30
MAX_FAILURES = 3



def allow(now: float | None = None) -> bool:
    global OPEN
    current = time.time() if now is None else now
    if OPEN and current - LAST_FAIL < RESET_AFTER_SECONDS:
        return False
    if OPEN:
        OPEN = False
    return True



def success() -> None:
    global FAILS, OPEN
    FAILS = 0
    OPEN = False



def fail(now: float | None = None) -> None:
    global FAILS, OPEN, LAST_FAIL
    FAILS += 1
    LAST_FAIL = time.time() if now is None else now
    if FAILS >= MAX_FAILURES:
        OPEN = True
