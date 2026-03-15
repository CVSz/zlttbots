from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class ServiceInstance:
    service: str
    host: str
    port: int
    version: str = "v1"
    healthy: bool = True

    @property
    def endpoint(self) -> str:
        return f"http://{self.host}:{self.port}"


class ServiceDiscovery:
    """In-memory service registry with health-aware lookups."""

    def __init__(self) -> None:
        self._services: dict[str, list[ServiceInstance]] = defaultdict(list)

    def register(self, instance: ServiceInstance) -> None:
        existing = [i for i in self._services[instance.service] if i.endpoint != instance.endpoint]
        existing.append(instance)
        self._services[instance.service] = existing

    def deregister(self, service: str, endpoint: str) -> None:
        self._services[service] = [i for i in self._services[service] if i.endpoint != endpoint]

    def resolve(self, service: str) -> list[ServiceInstance]:
        return [instance for instance in self._services[service] if instance.healthy]

    def snapshot(self) -> dict[str, list[str]]:
        return {name: [inst.endpoint for inst in instances] for name, instances in self._services.items()}
