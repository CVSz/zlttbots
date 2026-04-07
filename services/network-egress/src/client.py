import ipaddress
import logging
import socket
import time
from collections.abc import Mapping
from typing import Union
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]


class SafeHttpClient:
    """HTTP client with deterministic retry behavior and SSRF guardrails."""

    def __init__(
        self,
        timeout: int = 10,
        retries: int = 3,
        backoff: float = 0.5,
        allowed_hosts: set[str] | None = None,
    ):
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if retries <= 0:
            raise ValueError("retries must be > 0")
        if backoff < 0:
            raise ValueError("backoff must be >= 0")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.allowed_hosts = {host.lower() for host in allowed_hosts} if allowed_hosts else None
        self._session = requests.Session()
        self._session.trust_env = False

    @staticmethod
    def _is_blocked_address(address: IPAddress) -> bool:
        return (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
            or address.is_reserved
        )

    def _resolve_host_addresses(self, hostname: str) -> set[IPAddress]:
        resolved_addresses: set[IPAddress] = set()
        try:
            addrinfo = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as exc:
            raise ValueError(f"url host '{hostname}' could not be resolved") from exc

        for _, _, _, _, sockaddr in addrinfo:
            resolved_addresses.add(ipaddress.ip_address(sockaddr[0]))

        if not resolved_addresses:
            raise ValueError(f"url host '{hostname}' did not resolve to an address")
        return resolved_addresses

    def _validate_url(self, url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("url must use http or https")
        if not parsed.hostname:
            raise ValueError("url hostname is required")

        hostname = parsed.hostname.lower()
        if self.allowed_hosts is not None and hostname not in self.allowed_hosts:
            raise ValueError(f"url host '{hostname}' is not allowed")

        try:
            literal_ip = ipaddress.ip_address(hostname)
        except ValueError:
            for resolved_ip in self._resolve_host_addresses(hostname):
                if self._is_blocked_address(resolved_ip):
                    raise ValueError(
                        f"url host '{hostname}' resolved to a blocked address: {resolved_ip}"
                    )
            return

        if self._is_blocked_address(literal_ip):
            raise ValueError("private or loopback host targets are not allowed")

    def post(
        self,
        url: str,
        json: dict | list | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> requests.Response:
        self._validate_url(url)
        last_error: Exception | None = None
        last_response: requests.Response | None = None

        for attempt in range(1, self.retries + 1):
            try:
                response = self._session.post(url, json=json, headers=headers, timeout=self.timeout)
                if response.status_code < 500:
                    return response
                last_response = response
                logger.warning(
                    "Transient upstream response",
                    extra={"url": url, "attempt": attempt, "status_code": response.status_code},
                )
            except requests.RequestException as exc:
                last_error = exc
                logger.warning(
                    "Network request failed",
                    extra={"url": url, "attempt": attempt, "error": str(exc)},
                )
            if attempt < self.retries:
                time.sleep(self.backoff * (2 ** (attempt - 1)))

        if last_response is not None:
            raise RuntimeError(
                f"request failed after retries with status {last_response.status_code}: {url}"
            )
        raise RuntimeError(f"request failed after retries: {url}") from last_error
