from datetime import datetime, timedelta, timezone

from enterprise_maturity.governance import APIVersion, ChangeRecord, assert_backward_compatible
from enterprise_maturity.operations import ErrorBudgetPolicy, ProbeResult, SLO, Severity, SeverityPolicy, SeverityRule, SyntheticProbe
from enterprise_maturity.performance import AutoscalingAdvisor, QueueAdmissionController, WorkloadMetrics
from enterprise_maturity.resilience import CircuitBreaker, IdempotencyStore, RetryPolicy
from enterprise_maturity.roadmap import ROADMAP_IMPLEMENTATION
from enterprise_maturity.security import AccessToken, AuditEvent, AuditLogPipeline, RBACPolicy, SecretManager, SecretRotationPolicy


def test_secret_manager_rotation_due():
    manager = SecretManager(policy=SecretRotationPolicy(max_age_days=1))
    manager.put("db-password", "s3cr3t", rotated_at=datetime.now(timezone.utc) - timedelta(days=2))

    assert manager.get("db-password") == "s3cr3t"
    assert manager.due_for_rotation() == ["db-password"]


def test_rbac_policy_and_audit_pipeline():
    policy = RBACPolicy({"/admin/tenants": {"admin", "operator"}})
    assert policy.authorize("/admin/tenants", AccessToken("u1", frozenset({"admin"})))
    assert not policy.authorize("/admin/tenants", AccessToken("u2", frozenset({"viewer"})))

    pipeline = AuditLogPipeline()
    digest = pipeline.emit(AuditEvent(actor="u1", action="delete", resource="tenant/1", ip="127.0.0.1", result="ok"))
    assert len(digest) == 64
    assert len(pipeline.list_events()) == 1


def test_retry_and_idempotency_controls():
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("transient")
        return "ok"

    assert RetryPolicy(retries=2, base_delay_seconds=0).run(flaky) == "ok"
    store = IdempotencyStore()
    assert store.execute("req-1", lambda: 10) == 10
    assert store.execute("req-1", lambda: 99) == 10


def test_circuit_breaker_opens():
    breaker = CircuitBreaker(failure_threshold=1, open_interval_seconds=60)
    try:
        breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    except RuntimeError:
        pass

    try:
        breaker.call(lambda: "ok")
        assert False, "expected open circuit"
    except RuntimeError as exc:
        assert "open" in str(exc)


def test_slo_alerting_and_probe():
    slo = SLO("api", 0.999, 500, timedelta(minutes=5), "platform")
    budget = ErrorBudgetPolicy(slo)
    assert budget.remaining_budget(0.998) < 1

    policy = SeverityPolicy([
        SeverityRule("api-down", Severity.SEV1, 5, "oncall-a", "oncall-b"),
    ])
    assert policy.route("api-down").severity == Severity.SEV1

    probe = SyntheticProbe("health", lambda: ProbeResult("health", True, 40))
    assert probe.run().available


def test_governance_scaling_and_queue_admission():
    ChangeRecord("r1", "risk", "roll", "rollback", "approver").validate()
    assert_backward_compatible(APIVersion(1, 1, 0), APIVersion(1, 2, 0), has_breaking_change=False)

    advisor = AutoscalingAdvisor(min_replicas=1, max_replicas=5)
    recommendation = advisor.recommend(2, WorkloadMetrics(queue_depth=100, throughput_per_minute=10, cpu_utilization=0.8))
    assert recommendation.desired_replicas >= 3

    admission = QueueAdmissionController(critical_limit=1, best_effort_limit=1)
    assert admission.admit("critical")
    assert not admission.admit("critical")
    assert admission.admit("best_effort")


def test_roadmap_has_all_items():
    assert len(ROADMAP_IMPLEMENTATION) == 25
    assert ROADMAP_IMPLEMENTATION[0].id == 1
    assert ROADMAP_IMPLEMENTATION[-1].id == 25
