from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    retries: int = 3
    base_delay_seconds: float = 0.2
    max_delay_seconds: float = 2.0

    def run(self, func: Callable[[], T]) -> T:
        attempt = 0
        while True:
            try:
                return func()
            except Exception:
                if attempt >= self.retries:
                    raise
                delay = min(self.base_delay_seconds * (2**attempt), self.max_delay_seconds)
                time.sleep(delay)
                attempt += 1


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, open_interval_seconds: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.open_interval_seconds = open_interval_seconds
        self.failures = 0
        self._opened_at: datetime | None = None

    def _is_open(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self._opened_at is None:
            return False
        return now - self._opened_at < timedelta(seconds=self.open_interval_seconds)

    def call(self, func: Callable[[], T], now: datetime | None = None) -> T:
        now = now or datetime.now(timezone.utc)
        if self._is_open(now):
            raise RuntimeError("Circuit breaker is open")

        try:
            result = func()
            self.failures = 0
            self._opened_at = None
            return result
        except Exception:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self._opened_at = now
            raise


class IdempotencyStore:
    def __init__(self) -> None:
        self._responses: dict[str, object] = {}

    def execute(self, key: str, action: Callable[[], T]) -> T:
        if key in self._responses:
            return self._responses[key]  # type: ignore[return-value]
        value = action()
        self._responses[key] = value
        return value
