from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RenderJob:
    job_id: str
    gpu_memory_gb: int
    duration_s: int


@dataclass
class GPUNode:
    name: str
    total_memory_gb: int
    used_memory_gb: int = 0

    @property
    def available_gb(self) -> int:
        return self.total_memory_gb - self.used_memory_gb


class GPUScheduler:
    """Best-fit scheduler for GPU-bound rendering jobs."""

    def __init__(self, nodes: list[GPUNode]) -> None:
        if not nodes:
            raise ValueError("At least one GPU node is required")
        self.nodes = nodes

    def schedule(self, job: RenderJob) -> str:
        candidates = [n for n in self.nodes if n.available_gb >= job.gpu_memory_gb]
        if not candidates:
            raise LookupError(f"No GPU node can satisfy {job.gpu_memory_gb}GB for {job.job_id}")

        chosen = min(candidates, key=lambda n: n.available_gb)
        chosen.used_memory_gb += job.gpu_memory_gb
        return chosen.name

    def release(self, node_name: str, gpu_memory_gb: int) -> None:
        for node in self.nodes:
            if node.name == node_name:
                node.used_memory_gb = max(0, node.used_memory_gb - gpu_memory_gb)
                return
        raise KeyError(f"Unknown GPU node: {node_name}")
