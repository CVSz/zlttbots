from __future__ import annotations

from dataclasses import dataclass

from .autoscaling import AutoScaler, WorkerPool
from .queue_system import CentralQueue, QueueMessage


@dataclass(frozen=True)
class CrawlJob:
    job_id: str
    source: str
    keyword: str


class CrawlerClusterManager:
    """Distributed crawler coordinator using central queue + autoscaling."""

    def __init__(self, queue: CentralQueue, autoscaler: AutoScaler, pool: WorkerPool) -> None:
        self.queue = queue
        self.autoscaler = autoscaler
        self.pool = pool

    def submit(self, job: CrawlJob) -> None:
        self.queue.publish(
            QueueMessage(
                topic="crawl.jobs",
                payload={"job_id": job.job_id, "source": job.source, "keyword": job.keyword},
            )
        )

    def reconcile(self) -> int:
        backlog = self.queue.depth("crawl.jobs")
        return self.autoscaler.reconcile(self.pool, backlog)

    def dispatch_batch(self, batch_size: int) -> list[QueueMessage]:
        return self.queue.consume("crawl.jobs", batch_size=batch_size)
