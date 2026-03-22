from __future__ import annotations

import os

MAX_DAILY = float(os.getenv("MAX_DAILY_COST", "1000"))
spent = 0.0



def allow(cost: float) -> bool:
    global spent
    if spent + cost > MAX_DAILY:
        return False
    spent += cost
    return True



def reset() -> None:
    global spent
    spent = 0.0
