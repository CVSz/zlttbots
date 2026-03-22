from __future__ import annotations

import os

CAP = float(os.getenv("DAILY_CAP", "10000"))


class Treasury:
    def __init__(self) -> None:
        self.spent = 0.0

    def can_spend(self, amount: float) -> bool:
        return (self.spent + amount) <= CAP

    def spend(self, amount: float) -> bool:
        if self.can_spend(amount):
            self.spent += amount
            return True
        return False
