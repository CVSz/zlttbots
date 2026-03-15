from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkerPool:
    name: str
    min_workers: int
    max_workers: int
    target_backlog_per_worker: int
    current_workers: int


class AutoScaler:
    """Simple backlog-based autoscaler for worker pools."""

    def reconcile(self, pool: WorkerPool, backlog: int) -> int:
        if pool.target_backlog_per_worker <= 0:
            raise ValueError("target_backlog_per_worker must be > 0")

        desired = max(pool.min_workers, (backlog + pool.target_backlog_per_worker - 1) // pool.target_backlog_per_worker)
        desired = min(desired, pool.max_workers)
        pool.current_workers = desired
        return desired
