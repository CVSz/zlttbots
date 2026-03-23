from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from core.database import (
    PublishingJob,
    dequeue_publish_jobs,
    get_daily_counter,
    increase_daily_counter,
    put_dead_letter,
    record_publish_result,
)


@dataclass(frozen=True)
class PublishingPolicy:
    daily_target: int = 30
    retry_budget: int = 2


class DailyPublishingController:
    def __init__(self, policy: PublishingPolicy | None = None, day_provider: Callable[[], date] | None = None) -> None:
        self.policy = policy or PublishingPolicy()
        self.day_provider = day_provider or date.today

    def run_for_tenant(self, tenant_id: str, publish_fn: Callable[[PublishingJob], dict]) -> dict[str, int]:
        day_key = self.day_provider().isoformat()
        published_today = get_daily_counter(tenant_id, day_key)
        remaining_capacity = max(0, self.policy.daily_target - published_today)
        if remaining_capacity == 0:
            return {"processed": 0, "published": 0, "dead_lettered": 0, "remaining_capacity": 0}

        jobs = dequeue_publish_jobs(tenant_id, remaining_capacity)
        published = 0
        dead_lettered = 0

        for job in jobs:
            try:
                result = publish_fn(job)
                status = str(result.get("status", "submitted"))
                if status != "submitted":
                    raise RuntimeError(f"publish status={status}")
                increase_daily_counter(tenant_id, day_key)
                published += 1
                record_publish_result(
                    {
                        "tenant_id": tenant_id,
                        "product_id": job.product_id,
                        "video_id": job.video_id,
                        "network": (
                            result.get("network").value
                            if hasattr(result.get("network"), "value")
                            else str(result.get("network", "unknown"))
                        ),
                        "status": status,
                        "external_id": result.get("external_id"),
                    }
                )
            except Exception as exc:
                if job.retry_count < self.policy.retry_budget:
                    retry_job = PublishingJob(
                        tenant_id=job.tenant_id,
                        product_id=job.product_id,
                        video_id=job.video_id,
                        destination_url=job.destination_url,
                        retry_count=job.retry_count + 1,
                    )
                    # deterministic requeue to tail
                    from core.database import enqueue_publish_job

                    enqueue_publish_job(retry_job)
                else:
                    put_dead_letter(
                        {
                            "tenant_id": job.tenant_id,
                            "product_id": job.product_id,
                            "video_id": job.video_id,
                            "reason": str(exc),
                            "retry_count": job.retry_count,
                        }
                    )
                    dead_lettered += 1

        return {
            "processed": len(jobs),
            "published": published,
            "dead_lettered": dead_lettered,
            "remaining_capacity": max(0, self.policy.daily_target - get_daily_counter(tenant_id, day_key)),
        }
