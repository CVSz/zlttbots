from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Microservice:
    name: str
    domain: str
    runtime: str


@dataclass(frozen=True)
class CrawlerCluster:
    queue_backend: str
    scheduler: str
    max_workers: int


@dataclass(frozen=True)
class AIVideoPipeline:
    stages: tuple[str, ...]


@dataclass(frozen=True)
class UpgradeBlueprint:
    services: tuple[Microservice, ...]
    kafka_topics: tuple[str, ...]
    crawler_cluster: CrawlerCluster
    ai_video_pipeline: AIVideoPipeline
    admin_dashboard_modules: tuple[str, ...]
    frontend_apps: tuple[str, ...]
    kubernetes_namespaces: tuple[str, ...]
    cicd_stages: tuple[str, ...]

    def validate(self) -> None:
        if len(self.services) < 25:
            raise ValueError("Upgrade requires at least 25 microservices")
        if len(self.kafka_topics) < 8:
            raise ValueError("Upgrade requires a full Kafka event system")
        if self.crawler_cluster.max_workers < 12:
            raise ValueError("Distributed crawler cluster must support at least 12 workers")

        required_video_stages = {"ingest", "storyboard", "render", "qa", "publish"}
        if not required_video_stages.issubset(set(self.ai_video_pipeline.stages)):
            raise ValueError("AI video pipeline stages are incomplete")

        required_dashboard = {"tenants", "campaigns", "billing", "observability", "rbac"}
        if not required_dashboard.issubset(set(self.admin_dashboard_modules)):
            raise ValueError("Admin dashboard modules are incomplete")

        required_cicd = {"lint", "test", "build", "security-scan", "deploy"}
        if not required_cicd.issubset(set(self.cicd_stages)):
            raise ValueError("CI/CD stages are incomplete")


FULL_UPGRADE_BLUEPRINT = UpgradeBlueprint(
    services=(
        Microservice("gateway-api", "api", "node"),
        Microservice("identity-service", "security", "python"),
        Microservice("tenant-service", "core", "python"),
        Microservice("catalog-service", "commerce", "node"),
        Microservice("pricing-service", "commerce", "python"),
        Microservice("inventory-service", "commerce", "node"),
        Microservice("order-service", "commerce", "python"),
        Microservice("payment-service", "finance", "python"),
        Microservice("billing-service", "finance", "node"),
        Microservice("notification-service", "engagement", "node"),
        Microservice("analytics-service", "data", "python"),
        Microservice("event-collector", "data", "python"),
        Microservice("viral-predictor", "ai", "python"),
        Microservice("market-crawler", "crawler", "python"),
        Microservice("shopee-crawler", "crawler", "node"),
        Microservice("tiktok-shop-miner", "crawler", "node"),
        Microservice("arbitrage-engine", "trading", "python"),
        Microservice("ai-video-generator", "media", "node"),
        Microservice("gpu-renderer", "media", "python"),
        Microservice("asset-library", "media", "node"),
        Microservice("campaign-service", "marketing", "python"),
        Microservice("scheduler-service", "ops", "python"),
        Microservice("admin-panel-api", "admin", "node"),
        Microservice("frontend-web", "frontend", "nextjs"),
        Microservice("frontend-admin", "frontend", "nextjs"),
        Microservice("webhook-service", "integration", "python"),
        Microservice("audit-service", "security", "python"),
    ),
    kafka_topics=(
        "crawler.jobs",
        "crawler.results",
        "video.jobs",
        "video.completed",
        "campaign.events",
        "orders.events",
        "billing.events",
        "audit.events",
        "notifications.events",
    ),
    crawler_cluster=CrawlerCluster(queue_backend="kafka", scheduler="keda", max_workers=48),
    ai_video_pipeline=AIVideoPipeline(stages=("ingest", "storyboard", "voiceover", "render", "qa", "publish")),
    admin_dashboard_modules=("tenants", "campaigns", "billing", "observability", "rbac", "approvals"),
    frontend_apps=("storefront", "admin-console", "ops-console"),
    kubernetes_namespaces=("zlttbots-core", "zlttbots-data", "zlttbots-ai", "zlttbots-edge"),
    cicd_stages=("lint", "test", "build", "security-scan", "package", "deploy", "post-deploy-smoke"),
)
