from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class UpgradeComponent:
    """A deployable component introduced by the v3 enterprise upgrade."""

    name: str
    area: str
    criticality: str
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class TopicSpec:
    """Domain-event topic definition used by Kafka event backbone."""

    name: str
    partitions: int
    retention_hours: int


@dataclass(frozen=True)
class UpgradePhase:
    """A migration phase and its exit criteria."""

    name: str
    goals: tuple[str, ...]
    exit_criteria: tuple[str, ...]


class EnterpriseUpgradeV3:
    """Executable representation of the architecture-v3-enterprise plan."""

    def __init__(
        self,
        components: Iterable[UpgradeComponent],
        topics: Iterable[TopicSpec],
        phases: Iterable[UpgradePhase],
    ) -> None:
        self.components = tuple(components)
        self.topics = tuple(topics)
        self.phases = tuple(phases)

    @classmethod
    def default_blueprint(cls) -> "EnterpriseUpgradeV3":
        """Build the default v3 enterprise upgrade blueprint."""
        components = (
            UpgradeComponent("traefik-gateway", "gateway", "high", ("oidc-auth",)),
            UpgradeComponent("kafka-backbone", "eventing", "high", ("redis",)),
            UpgradeComponent("video-pipeline", "ai", "high", ("kafka-backbone", "gpu-renderer")),
            UpgradeComponent("crawler-fleet", "crawlers", "high", ("kafka-backbone",)),
            UpgradeComponent("otel-observability", "operations", "medium", ("prometheus", "loki", "jaeger")),
            UpgradeComponent("n8n-orchestrator", "automation", "medium", ("kafka-backbone", "video-pipeline")),
            UpgradeComponent("k8s-runtime", "infrastructure", "high", ("traefik-gateway", "otel-observability")),
        )
        topics = (
            TopicSpec("crawl.jobs", partitions=12, retention_hours=72),
            TopicSpec("video.render", partitions=6, retention_hours=48),
            TopicSpec("tiktok.upload", partitions=6, retention_hours=48),
            TopicSpec("analytics.events", partitions=18, retention_hours=168),
        )
        phases = (
            UpgradePhase(
                "phase-1-foundation",
                goals=(
                    "Introduce Traefik in parallel with NGINX",
                    "Enable Kafka dual-publish for core producers",
                    "Deploy baseline observability stack",
                ),
                exit_criteria=(
                    "Gateway routes pass smoke checks",
                    "Critical producers emit to Kafka topics",
                    "SLI dashboards available for APIs and workers",
                ),
            ),
            UpgradePhase(
                "phase-2-service-refactor",
                goals=(
                    "Split AI pipeline into explicit service stages",
                    "Normalize crawler contracts and payloads",
                    "Enforce tenant-aware auth middleware",
                ),
                exit_criteria=(
                    "AI stages deploy independently",
                    "Contract checks pass for top service edges",
                    "Privileged APIs require scoped tokens",
                ),
            ),
            UpgradePhase(
                "phase-3-kubernetes",
                goals=(
                    "Migrate APIs and workers to Kubernetes",
                    "Enable HPA for stateless workloads",
                    "Provision dedicated GPU node pool",
                ),
                exit_criteria=(
                    "Compose no longer required in production",
                    "HPA reacts within SLO thresholds",
                    "GPU workloads isolated to dedicated nodes",
                ),
            ),
            UpgradePhase(
                "phase-4-enterprise-operations",
                goals=(
                    "Deploy n8n workflows for end-to-end automation",
                    "Enable canary or blue/green delivery",
                    "Operationalize SLOs and DR drills",
                ),
                exit_criteria=(
                    "Workflow automation completes without manual hand-offs",
                    "Progressive delivery rollback tested",
                    "DR drills meet declared RPO/RTO targets",
                ),
            ),
        )
        return cls(components=components, topics=topics, phases=phases)

    def validate(self) -> None:
        """Validate structural integrity of the blueprint."""
        self._require_unique([component.name for component in self.components], "component")
        self._require_unique([topic.name for topic in self.topics], "topic")
        self._require_unique([phase.name for phase in self.phases], "phase")

        component_names = {component.name for component in self.components}
        for component in self.components:
            for dependency in component.dependencies:
                if dependency in {"redis", "prometheus", "loki", "jaeger", "oidc-auth", "gpu-renderer"}:
                    continue
                if dependency not in component_names:
                    raise ValueError(f"Unknown dependency '{dependency}' for component '{component.name}'")

        for topic in self.topics:
            if topic.partitions <= 0:
                raise ValueError(f"Topic '{topic.name}' must have at least one partition")
            if topic.retention_hours <= 0:
                raise ValueError(f"Topic '{topic.name}' must have a positive retention policy")

    def phase_checklist(self, phase_name: str) -> tuple[str, ...]:
        for phase in self.phases:
            if phase.name == phase_name:
                return phase.goals + phase.exit_criteria
        raise KeyError(f"Unknown phase: {phase_name}")

    @staticmethod
    def _require_unique(values: list[str], label: str) -> None:
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate {label} names detected in v3 upgrade blueprint")
