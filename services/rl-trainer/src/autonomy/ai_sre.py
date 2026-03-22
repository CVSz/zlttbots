from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Incident:
    name: str
    severity: str
    recommendation: str


RUNBOOKS = {
    "high_cpu": Incident("high_cpu", "warning", "Scale the busiest worker or reduce concurrency."),
    "oom": Incident("oom", "critical", "Restart the affected service after capturing a memory snapshot."),
    "kafka_lag": Incident("kafka_lag", "warning", "Increase consumer capacity or inspect the broker backlog."),
}


def detect(metrics: dict[str, float]) -> Incident | None:
    if metrics.get("cpu", 0.0) > 0.9:
        return RUNBOOKS["high_cpu"]
    if metrics.get("oom", 0.0) > 0:
        return RUNBOOKS["oom"]
    if metrics.get("kafka_lag", 0.0) > 1000:
        return RUNBOOKS["kafka_lag"]
    return None


def evaluate(fetch_metrics: Callable[[], dict[str, float]]) -> Incident | None:
    incident = detect(fetch_metrics())
    if incident:
        log.warning("ai-sre detected %s (%s): %s", incident.name, incident.severity, incident.recommendation)
    return incident
