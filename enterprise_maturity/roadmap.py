from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoadmapItem:
    id: int
    title: str
    implementation: str


ROADMAP_IMPLEMENTATION: tuple[RoadmapItem, ...] = (
    RoadmapItem(1, "Centralized secrets management", "enterprise_maturity.security.SecretManager"),
    RoadmapItem(2, "SSO + RBAC for admin panel and internal APIs", "enterprise_maturity.security.RBACPolicy"),
    RoadmapItem(3, "Audit log pipeline for privileged actions", "enterprise_maturity.security.AuditLogPipeline"),
    RoadmapItem(4, "Automated SAST/DAST and container image scanning in CI", ".github/workflows/zlttbots-ci.yml"),
    RoadmapItem(5, "CI/CD gates before deploy", ".github/workflows/zlttbots-ci.yml"),
    RoadmapItem(6, "Environment promotion workflow with approvals", ".github/workflows/zlttbots-ci.yml"),
    RoadmapItem(7, "Define and track SLOs per service", "enterprise_maturity.operations.SLO"),
    RoadmapItem(8, "Circuit breakers, retries with backoff, idempotency keys", "enterprise_maturity.resilience"),
    RoadmapItem(9, "Unified logs, metrics, traces", "docs/operations/monitoring.md"),
    RoadmapItem(10, "Runbooks for every production service and worker", "docs/operations/runbooks"),
    RoadmapItem(11, "Alert routing with severity policy and ownership", "enterprise_maturity.operations.SeverityPolicy"),
    RoadmapItem(12, "Capacity dashboards and error budget views", "docs/operations/slo-catalog.md"),
    RoadmapItem(13, "Synthetic checks for public and key internal paths", "enterprise_maturity.operations.SyntheticProbe"),
    RoadmapItem(14, "IaC policy checks for k8s and docker changes", "infrastructure/scripts/check-iac-policy.sh"),
    RoadmapItem(15, "Versioned API contracts and compatibility verification", "enterprise_maturity.governance.assert_backward_compatible"),
    RoadmapItem(16, "Change management template for high-risk rollouts", "enterprise_maturity.governance.ChangeRecord"),
    RoadmapItem(17, "Data retention + PII controls", "docs/security/audit-event-schema.md"),
    RoadmapItem(18, "Multi-AZ database and Redis HA with failover playbooks", "docs/operations/disaster-recovery.md"),
    RoadmapItem(19, "Blue/green or canary deployments", "infrastructure/ci/deploy.sh"),
    RoadmapItem(20, "Disaster recovery with RPO/RTO targets and drills", "docs/operations/disaster-recovery.md"),
    RoadmapItem(21, "Autoscaling tuning with workload metrics", "enterprise_maturity.performance.AutoscalingAdvisor"),
    RoadmapItem(22, "Workload profiling", "docs/infrastructure/scaling.md"),
    RoadmapItem(23, "Cost allocation tags and cloud spend dashboard", "infrastructure/k8s/config/configmap.yaml"),
    RoadmapItem(24, "Queue prioritization and admission control", "enterprise_maturity.performance.QueueAdmissionController"),
    RoadmapItem(25, "Periodic rightsizing for compute-heavy services", "infrastructure/scripts/zlttbots-resource-optimizer.sh"),
)
