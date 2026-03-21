from __future__ import annotations

import random
import time

from rollback import backup, rollback


def loop() -> None:
    backup()
    while True:
        perf = random.random()
        if perf < 0.2:
            print("⚠️ PERFORMANCE DROP → rollback")
            rollback()
        time.sleep(15)


if __name__ == "__main__":
    loop()
