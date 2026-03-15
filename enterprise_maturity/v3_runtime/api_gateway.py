from __future__ import annotations

from dataclasses import dataclass

from .service_discovery import ServiceDiscovery


@dataclass(frozen=True)
class Route:
    path: str
    service: str


class APIGateway:
    """Path-based API gateway backed by dynamic service discovery."""

    def __init__(self, discovery: ServiceDiscovery) -> None:
        self.discovery = discovery
        self._routes: dict[str, Route] = {}
        self._round_robin_idx: dict[str, int] = {}

    def add_route(self, route: Route) -> None:
        self._routes[route.path] = route

    def route(self, path: str) -> str:
        route = self._routes.get(path)
        if route is None:
            raise KeyError(f"No route configured for {path}")

        candidates = self.discovery.resolve(route.service)
        if not candidates:
            raise LookupError(f"No healthy instance found for service={route.service}")

        idx = self._round_robin_idx.get(route.service, 0) % len(candidates)
        self._round_robin_idx[route.service] = idx + 1
        return f"{candidates[idx].endpoint}{path}"

    def routes(self) -> dict[str, str]:
        return {path: route.service for path, route in self._routes.items()}
