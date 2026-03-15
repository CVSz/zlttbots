from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkloadMetrics:
    queue_depth: int
    throughput_per_minute: int
    cpu_utilization: float


@dataclass(frozen=True)
class ScalingRecommendation:
    desired_replicas: int
    reason: str


class AutoscalingAdvisor:
    def __init__(self, min_replicas: int = 2, max_replicas: int = 20) -> None:
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas

    def recommend(self, current_replicas: int, metrics: WorkloadMetrics) -> ScalingRecommendation:
        if metrics.queue_depth > metrics.throughput_per_minute * 2:
            return ScalingRecommendation(min(self.max_replicas, current_replicas + 2), "queue backlog")
        if metrics.cpu_utilization > 0.75:
            return ScalingRecommendation(min(self.max_replicas, current_replicas + 1), "high CPU")
        if metrics.cpu_utilization < 0.30 and metrics.queue_depth == 0:
            return ScalingRecommendation(max(self.min_replicas, current_replicas - 1), "idle capacity")
        return ScalingRecommendation(current_replicas, "steady state")


class QueueAdmissionController:
    def __init__(self, critical_limit: int = 100, best_effort_limit: int = 25) -> None:
        self.critical_limit = critical_limit
        self.best_effort_limit = best_effort_limit
        self._inflight = {"critical": 0, "best_effort": 0}

    def admit(self, priority: str) -> bool:
        if priority == "critical":
            if self._inflight["critical"] >= self.critical_limit:
                return False
            self._inflight["critical"] += 1
            return True
        if self._inflight["best_effort"] >= self.best_effort_limit:
            return False
        self._inflight["best_effort"] += 1
        return True

    def complete(self, priority: str) -> None:
        lane = "critical" if priority == "critical" else "best_effort"
        self._inflight[lane] = max(0, self._inflight[lane] - 1)
