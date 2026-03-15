from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Callable


@dataclass(frozen=True)
class SLO:
    service: str
    availability_target: float
    p95_latency_ms: int
    data_freshness_slo: timedelta
    owner: str


@dataclass(frozen=True)
class ErrorBudgetPolicy:
    slo: SLO

    def remaining_budget(self, observed_availability: float) -> float:
        allowed_error = 1 - self.slo.availability_target
        consumed_error = max(0.0, 1 - observed_availability)
        if allowed_error == 0:
            return 0.0
        return max(0.0, 1 - (consumed_error / allowed_error))


class Severity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


@dataclass(frozen=True)
class SeverityRule:
    name: str
    severity: Severity
    response_sla_minutes: int
    primary_owner: str
    secondary_owner: str


class SeverityPolicy:
    def __init__(self, rules: list[SeverityRule]) -> None:
        self._rules = {rule.name: rule for rule in rules}

    def route(self, alert_name: str) -> SeverityRule:
        if alert_name not in self._rules:
            raise KeyError(f"Alert '{alert_name}' is unmapped")
        return self._rules[alert_name]


@dataclass(frozen=True)
class ProbeResult:
    name: str
    available: bool
    latency_ms: int


class SyntheticProbe:
    def __init__(self, name: str, check: Callable[[], ProbeResult]) -> None:
        self.name = name
        self._check = check

    def run(self) -> ProbeResult:
        return self._check()
