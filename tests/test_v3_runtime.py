from pathlib import Path

from enterprise_maturity.v3_runtime import (
    APIGateway,
    AutoScaler,
    CentralQueue,
    CrawlerClusterManager,
    CrawlJob,
    EnterpriseRuntime,
    GPUScheduler,
    GPUNode,
    PolicyFix,
    PolicyViolation,
    QueueMessage,
    RenderJob,
    RegionalMetric,
    Route,
    ServiceDiscovery,
    ServiceInstance,
    StageTiming,
    WorkerPool,
)
from enterprise_maturity.v3_runtime.deployment_pipeline import NotificationBridge


def test_api_gateway_uses_service_discovery_round_robin() -> None:
    discovery = ServiceDiscovery()
    discovery.register(ServiceInstance("crawler", "crawler-a", 9400))
    discovery.register(ServiceInstance("crawler", "crawler-b", 9401))

    gateway = APIGateway(discovery)
    gateway.add_route(Route(path="/crawl", service="crawler"))

    assert gateway.route("/crawl") == "http://crawler-a:9400/crawl"
    assert gateway.route("/crawl") == "http://crawler-b:9401/crawl"


def test_central_queue_publish_consume() -> None:
    queue = CentralQueue()
    queue.publish(QueueMessage(topic="analytics.events", payload={"event": "view"}))
    queue.publish(QueueMessage(topic="analytics.events", payload={"event": "click"}))

    assert queue.depth("analytics.events") == 2
    payloads = [m.payload["event"] for m in queue.consume("analytics.events", batch_size=2)]
    assert payloads == ["view", "click"]


def test_autoscaling_worker_pool() -> None:
    scaler = AutoScaler()
    pool = WorkerPool(
        name="crawler-worker",
        min_workers=3,
        max_workers=20,
        target_backlog_per_worker=5,
        current_workers=3,
    )

    assert scaler.reconcile(pool, backlog=0) == 3
    assert scaler.reconcile(pool, backlog=36) == 8
    assert scaler.reconcile(pool, backlog=400) == 20


def test_gpu_scheduler_assigns_best_fit() -> None:
    scheduler = GPUScheduler([GPUNode("gpu-1", total_memory_gb=24), GPUNode("gpu-2", total_memory_gb=48)])

    first = scheduler.schedule(RenderJob(job_id="a", gpu_memory_gb=12, duration_s=10))
    second = scheduler.schedule(RenderJob(job_id="b", gpu_memory_gb=20, duration_s=10))

    assert first == "gpu-1"
    assert second == "gpu-2"


def test_distributed_crawler_cluster_reconcile_and_dispatch() -> None:
    queue = CentralQueue()
    scaler = AutoScaler()
    pool = WorkerPool("crawler-worker", min_workers=2, max_workers=10, target_backlog_per_worker=2, current_workers=2)
    cluster = CrawlerClusterManager(queue, scaler, pool)

    for idx in range(7):
        cluster.submit(CrawlJob(job_id=f"job-{idx}", source="shopee", keyword="mouse"))

    desired = cluster.reconcile()
    dispatched = cluster.dispatch_batch(batch_size=3)

    assert desired == 4
    assert len(dispatched) == 3
    assert queue.depth("crawl.jobs") == 4


def test_enterprise_runtime_bootstrap_and_components() -> None:
    runtime = EnterpriseRuntime()
    runtime.bootstrap()

    route_target = runtime.gateway.route("/crawl")
    runtime.enqueue_domain_event("video.render", {"video_id": "v1"})
    assigned = runtime.schedule_render(job_id="render-1", gpu_memory_gb=8, duration_s=60)

    assert route_target.startswith("http://market-crawler")
    assert runtime.queue.depth("video.render") == 1
    assert assigned in {"gpu-a10-1", "gpu-a10-2", "gpu-l4-1"}


def test_multi_region_canary_auto_rollback_and_pipeline_optimization() -> None:
    runtime = EnterpriseRuntime()

    assessment = runtime.evaluate_multi_region_canary(
        [
            RegionalMetric("us-east-1", baseline_error_rate=0.01, canary_error_rate=0.015, baseline_latency_ms=120, canary_latency_ms=140),
            RegionalMetric("eu-west-1", baseline_error_rate=0.01, canary_error_rate=0.05, baseline_latency_ms=110, canary_latency_ms=220),
        ]
    )
    assert assessment.decision == "rollback"
    assert assessment.rollback_regions == ("eu-west-1",)

    plan = runtime.optimize_pipeline_execution(
        [
            StageTiming(stage="lint", duration_seconds=40, parallelizable=True),
            StageTiming(stage="type-check", duration_seconds=55, parallelizable=True),
            StageTiming(stage="security-scan", duration_seconds=90, parallelizable=True),
            StageTiming(stage="integration-tests", duration_seconds=120, parallelizable=False),
            StageTiming(stage="deploy", duration_seconds=45, parallelizable=False),
        ]
    )

    assert plan.ordered_groups[0] == ("security-scan", "type-check", "lint")
    assert plan.predicted_duration_seconds == 255
    assert plan.recommended_timeout_seconds > plan.predicted_duration_seconds


def test_policy_analytics_persistence_manifest_healing_and_notifications(tmp_path: Path) -> None:
    runtime = EnterpriseRuntime(policy_db_path=str(tmp_path / "policy.db"))

    violation_id = runtime.record_policy_violation(
        PolicyViolation(
            policy="container.readOnlyRootFilesystem",
            resource="deployment/renderer",
            severity="high",
            details="Container filesystem is writable",
        )
    )
    fix_id = runtime.record_policy_fix(
        PolicyFix(
            violation_id=violation_id,
            action="Set securityContext.readOnlyRootFilesystem=true",
            actor="auto-healer",
            notes="Applied and verified via policy engine",
        )
    )
    snapshot = runtime.policy_store.snapshot()

    assert violation_id == 1
    assert fix_id == 1
    assert len(snapshot["violations"]) == 1
    assert len(snapshot["fixes"]) == 1

    docker_drift = runtime.detect_manifest_drift(
        kind="docker",
        name="renderer-stack",
        desired={"services": {"renderer": {"restart": "always"}}},
        current={"services": {"renderer": {"restart": "on-failure"}}},
    )
    assert docker_drift is not None
    healed = runtime.heal_manifest(docker_drift)
    assert healed == {"services": {"renderer": {"restart": "always"}}}

    runtime.notification_bridge = NotificationBridge(telegram_enabled=True, discord_enabled=True)
    notifications = runtime.prepare_auto_fix_notifications(
        message="Policy auto-fix applied",
        metadata={"violation_id": violation_id, "fix_id": fix_id},
    )
    assert set(notifications.keys()) == {"telegram", "discord"}
