from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from typing import Iterable


@dataclass(frozen=True)
class RegionalMetric:
    region: str
    baseline_error_rate: float
    canary_error_rate: float
    baseline_latency_ms: int
    canary_latency_ms: int


@dataclass(frozen=True)
class CanaryAssessment:
    decision: str
    safe_regions: tuple[str, ...]
    rollback_regions: tuple[str, ...]
    reason: str


class MultiRegionCanaryManager:
    """Evaluates canary health per-region and enforces automatic rollback decisions."""

    def __init__(self, max_error_delta: float = 0.02, max_latency_delta_ms: int = 50) -> None:
        if max_error_delta <= 0:
            raise ValueError("max_error_delta must be positive")
        if max_latency_delta_ms <= 0:
            raise ValueError("max_latency_delta_ms must be positive")
        self.max_error_delta = max_error_delta
        self.max_latency_delta_ms = max_latency_delta_ms

    def assess(self, metrics: Iterable[RegionalMetric]) -> CanaryAssessment:
        metric_list = tuple(metrics)
        if not metric_list:
            raise ValueError("at least one region metric is required")

        safe_regions: list[str] = []
        rollback_regions: list[str] = []
        reasons: list[str] = []

        for item in metric_list:
            self._validate_metric(item)
            error_delta = item.canary_error_rate - item.baseline_error_rate
            latency_delta = item.canary_latency_ms - item.baseline_latency_ms

            if error_delta > self.max_error_delta or latency_delta > self.max_latency_delta_ms:
                rollback_regions.append(item.region)
                reasons.append(
                    f"{item.region}: error_delta={error_delta:.4f}, latency_delta_ms={latency_delta}"
                )
            else:
                safe_regions.append(item.region)

        if rollback_regions:
            return CanaryAssessment(
                decision="rollback",
                safe_regions=tuple(sorted(safe_regions)),
                rollback_regions=tuple(sorted(rollback_regions)),
                reason="; ".join(sorted(reasons)),
            )

        return CanaryAssessment(
            decision="promote",
            safe_regions=tuple(sorted(safe_regions)),
            rollback_regions=(),
            reason="All regions are within canary thresholds",
        )

    @staticmethod
    def _validate_metric(metric: RegionalMetric) -> None:
        if not metric.region:
            raise ValueError("region must be set")
        if metric.baseline_error_rate < 0 or metric.canary_error_rate < 0:
            raise ValueError("error rates cannot be negative")
        if metric.baseline_latency_ms <= 0 or metric.canary_latency_ms <= 0:
            raise ValueError("latency must be positive")


@dataclass(frozen=True)
class StageTiming:
    stage: str
    duration_seconds: int
    parallelizable: bool


@dataclass(frozen=True)
class OptimizationPlan:
    ordered_groups: tuple[tuple[str, ...], ...]
    predicted_duration_seconds: int
    recommended_timeout_seconds: int


class PipelineAIOptimizer:
    """Deterministic optimization planner for CI/CD pipeline execution time."""

    def optimize(self, timings: Iterable[StageTiming]) -> OptimizationPlan:
        timeline = tuple(timings)
        if not timeline:
            raise ValueError("timings are required")

        self._validate(timeline)
        serial = [item for item in timeline if not item.parallelizable]
        parallel = [item for item in timeline if item.parallelizable]

        parallel_sorted = sorted(parallel, key=lambda item: (-item.duration_seconds, item.stage))
        serial_sorted = sorted(serial, key=lambda item: item.stage)

        ordered_groups: list[tuple[str, ...]] = []
        if parallel_sorted:
            ordered_groups.append(tuple(item.stage for item in parallel_sorted))
        ordered_groups.extend((item.stage,) for item in serial_sorted)

        parallel_cost = max((item.duration_seconds for item in parallel_sorted), default=0)
        serial_cost = sum(item.duration_seconds for item in serial_sorted)
        predicted = parallel_cost + serial_cost
        timeout = int(predicted * 1.2) + 30

        return OptimizationPlan(
            ordered_groups=tuple(ordered_groups),
            predicted_duration_seconds=predicted,
            recommended_timeout_seconds=timeout,
        )

    @staticmethod
    def _validate(stages: tuple[StageTiming, ...]) -> None:
        seen: set[str] = set()
        for stage in stages:
            if not stage.stage:
                raise ValueError("stage name cannot be empty")
            if stage.duration_seconds <= 0:
                raise ValueError("duration must be positive")
            if stage.stage in seen:
                raise ValueError(f"duplicate stage found: {stage.stage}")
            seen.add(stage.stage)


@dataclass(frozen=True)
class PolicyViolation:
    policy: str
    resource: str
    severity: str
    details: str


@dataclass(frozen=True)
class PolicyFix:
    violation_id: int
    action: str
    actor: str
    notes: str


class PolicyAnalyticsStore:
    """Persists policy violations and fixes for analytics workloads."""

    def __init__(self, db_path: str = ":memory:") -> None:
        if not db_path:
            raise ValueError("db_path cannot be empty")
        self.db_path = db_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS policy_fixes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    violation_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (violation_id) REFERENCES policy_violations(id)
                )
                """
            )

    def record_violation(self, violation: PolicyViolation) -> int:
        self._validate_violation(violation)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO policy_violations (policy, resource, severity, details, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    violation.policy,
                    violation.resource,
                    violation.severity,
                    violation.details,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def record_fix(self, fix: PolicyFix) -> int:
        self._validate_fix(fix)
        with self._connect() as conn:
            violation = conn.execute(
                "SELECT id FROM policy_violations WHERE id = ?",
                (fix.violation_id,),
            ).fetchone()
            if violation is None:
                raise KeyError(f"violation_id not found: {fix.violation_id}")
            cursor = conn.execute(
                """
                INSERT INTO policy_fixes (violation_id, action, actor, notes, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fix.violation_id,
                    fix.action,
                    fix.actor,
                    fix.notes,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def snapshot(self) -> dict[str, tuple[dict[str, object], ...]]:
        with self._connect() as conn:
            violations = tuple(
                {
                    "id": row[0],
                    "policy": row[1],
                    "resource": row[2],
                    "severity": row[3],
                    "details": row[4],
                }
                for row in conn.execute("SELECT id, policy, resource, severity, details FROM policy_violations ORDER BY id")
            )
            fixes = tuple(
                {
                    "id": row[0],
                    "violation_id": row[1],
                    "action": row[2],
                    "actor": row[3],
                    "notes": row[4],
                }
                for row in conn.execute("SELECT id, violation_id, action, actor, notes FROM policy_fixes ORDER BY id")
            )
        return {"violations": violations, "fixes": fixes}

    @staticmethod
    def _validate_violation(violation: PolicyViolation) -> None:
        if not all((violation.policy, violation.resource, violation.severity, violation.details)):
            raise ValueError("policy violation fields must not be empty")

    @staticmethod
    def _validate_fix(fix: PolicyFix) -> None:
        if fix.violation_id <= 0:
            raise ValueError("violation_id must be positive")
        if not all((fix.action, fix.actor, fix.notes)):
            raise ValueError("policy fix fields must not be empty")


@dataclass(frozen=True)
class ManifestDrift:
    kind: str
    name: str
    desired: dict[str, object]
    current: dict[str, object]


class ManifestSelfHealer:
    """Detects and remediates drift in Docker Compose and Helm manifests."""

    def detect_drift(self, kind: str, name: str, desired: dict[str, object], current: dict[str, object]) -> ManifestDrift | None:
        self._validate(kind, name, desired, current)
        if desired == current:
            return None
        return ManifestDrift(kind=kind, name=name, desired=desired, current=current)

    def heal(self, drift: ManifestDrift) -> dict[str, object]:
        self._validate(drift.kind, drift.name, drift.desired, drift.current)
        if drift.kind not in {"docker", "helm"}:
            raise ValueError(f"unsupported manifest kind: {drift.kind}")
        return json.loads(json.dumps(drift.desired))

    @staticmethod
    def _validate(kind: str, name: str, desired: dict[str, object], current: dict[str, object]) -> None:
        if kind not in {"docker", "helm"}:
            raise ValueError("kind must be 'docker' or 'helm'")
        if not name:
            raise ValueError("name must not be empty")
        if not desired:
            raise ValueError("desired manifest cannot be empty")
        if not current:
            raise ValueError("current manifest cannot be empty")


class NotificationBridge:
    """Formats optional Telegram/Discord notifications for auto-fix workflows."""

    def __init__(self, telegram_enabled: bool = False, discord_enabled: bool = False) -> None:
        self.telegram_enabled = telegram_enabled
        self.discord_enabled = discord_enabled

    def format_auto_fix_notification(self, message: str, metadata: dict[str, object]) -> dict[str, dict[str, object]]:
        if not message:
            raise ValueError("message must not be empty")
        payload = {
            "message": message,
            "metadata": metadata,
        }
        targets: dict[str, dict[str, object]] = {}
        if self.telegram_enabled:
            targets["telegram"] = payload
        if self.discord_enabled:
            targets["discord"] = payload
        return targets
