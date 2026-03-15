from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Dict, Iterable


@dataclass(frozen=True)
class SecretRecord:
    name: str
    value: str
    rotated_at: datetime


@dataclass(frozen=True)
class SecretRotationPolicy:
    max_age_days: int = 30

    def is_rotation_due(self, rotated_at: datetime, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now - rotated_at >= timedelta(days=self.max_age_days)


class SecretManager:
    """In-memory secret manager representing managed-secret backends."""

    def __init__(self, policy: SecretRotationPolicy | None = None) -> None:
        self._policy = policy or SecretRotationPolicy()
        self._secrets: Dict[str, SecretRecord] = {}

    def put(self, name: str, value: str, rotated_at: datetime | None = None) -> None:
        self._secrets[name] = SecretRecord(
            name=name,
            value=value,
            rotated_at=rotated_at or datetime.now(timezone.utc),
        )

    def get(self, name: str) -> str:
        if name not in self._secrets:
            raise KeyError(f"Secret '{name}' was not found in the managed store")
        return self._secrets[name].value

    def due_for_rotation(self, now: datetime | None = None) -> list[str]:
        now = now or datetime.now(timezone.utc)
        return [
            secret.name
            for secret in self._secrets.values()
            if self._policy.is_rotation_due(secret.rotated_at, now=now)
        ]


@dataclass(frozen=True)
class AccessToken:
    subject: str
    roles: frozenset[str]


class RBACPolicy:
    def __init__(self, permission_map: Dict[str, Iterable[str]]) -> None:
        self._permission_map = {route: frozenset(roles) for route, roles in permission_map.items()}

    def authorize(self, route: str, token: AccessToken) -> bool:
        required_roles = self._permission_map.get(route)
        if required_roles is None:
            return False
        return bool(required_roles.intersection(token.roles))


@dataclass(frozen=True)
class AuditEvent:
    actor: str
    action: str
    resource: str
    ip: str
    result: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def digest(self) -> str:
        payload = f"{self.actor}|{self.action}|{self.resource}|{self.ip}|{self.result}|{self.timestamp.isoformat()}"
        return sha256(payload.encode("utf-8")).hexdigest()


class AuditLogPipeline:
    """Append-only in-memory sink with verifiable chaining."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> str:
        self._events.append(event)
        return event.digest

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
