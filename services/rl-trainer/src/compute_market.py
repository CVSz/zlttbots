from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkerNode:
    worker_id: str
    capacity: float
    price_per_unit: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ComputeMarket:
    def __init__(self) -> None:
        self.workers: list[WorkerNode] = []

    def register(self, worker_id: str, capacity: float, price_per_unit: float = 1.0, **metadata: Any) -> WorkerNode:
        worker = WorkerNode(
            worker_id=worker_id,
            capacity=capacity,
            price_per_unit=price_per_unit,
            metadata=metadata,
        )
        self.workers.append(worker)
        return worker

    def bid(self, job_demand: float) -> list[dict[str, float | str]]:
        bids: list[dict[str, float | str]] = []
        for worker in self.workers:
            if worker.capacity < job_demand:
                continue
            bids.append(
                {
                    "worker_id": worker.worker_id,
                    "capacity": worker.capacity,
                    "price": worker.price_per_unit * job_demand,
                    "score": worker.capacity / max(worker.price_per_unit, 1e-8),
                }
            )
        return sorted(bids, key=lambda item: (-float(item["score"]), float(item["price"])))

    def assign(self, job: dict[str, Any]) -> WorkerNode | None:
        demand = float(job.get("demand", 1.0))
        bids = self.bid(demand)
        if not bids:
            return None
        best_worker_id = str(bids[0]["worker_id"])
        return next(worker for worker in self.workers if worker.worker_id == best_worker_id)
