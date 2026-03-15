from __future__ import annotations

from .api_gateway import APIGateway, Route
from .autoscaling import AutoScaler, WorkerPool
from .crawler_cluster import CrawlerClusterManager
from .gpu_scheduler import GPUNode, GPUScheduler, RenderJob
from .queue_system import CentralQueue, QueueMessage
from .service_discovery import ServiceDiscovery, ServiceInstance


class EnterpriseRuntime:
    """Reference composition of v3 enterprise building blocks."""

    def __init__(self) -> None:
        self.discovery = ServiceDiscovery()
        self.gateway = APIGateway(self.discovery)
        self.queue = CentralQueue()
        self.autoscaler = AutoScaler()

        self.crawler_pool = WorkerPool(
            name="crawler-worker",
            min_workers=3,
            max_workers=100,
            target_backlog_per_worker=8,
            current_workers=3,
        )
        self.crawler_cluster = CrawlerClusterManager(self.queue, self.autoscaler, self.crawler_pool)

        self.gpu_scheduler = GPUScheduler(
            nodes=[
                GPUNode(name="gpu-a10-1", total_memory_gb=24),
                GPUNode(name="gpu-a10-2", total_memory_gb=24),
                GPUNode(name="gpu-l4-1", total_memory_gb=48),
            ]
        )

    def bootstrap(self) -> None:
        self.discovery.register(ServiceInstance("market-crawler", "market-crawler", 9400))
        self.discovery.register(ServiceInstance("market-crawler", "market-crawler-canary", 9401))
        self.discovery.register(ServiceInstance("viral-predictor", "viral-predictor", 9100))

        self.gateway.add_route(Route(path="/crawl", service="market-crawler"))
        self.gateway.add_route(Route(path="/predict", service="viral-predictor"))

    def enqueue_domain_event(self, topic: str, payload: dict[str, object]) -> None:
        self.queue.publish(QueueMessage(topic=topic, payload=payload))

    def schedule_render(self, job_id: str, gpu_memory_gb: int, duration_s: int) -> str:
        return self.gpu_scheduler.schedule(
            RenderJob(job_id=job_id, gpu_memory_gb=gpu_memory_gb, duration_s=duration_s)
        )
