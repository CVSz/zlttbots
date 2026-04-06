from __future__ import annotations

import ipaddress
import json
import socket
import threading
from typing import Iterable


class P2PAgent:
    def __init__(
        self,
        weights: Iterable[float],
        port: int = 9000,
        host: str = "127.0.0.1",
        allow_wildcard_bind: bool = False,
    ) -> None:
        self.weights = [float(value) for value in weights]
        self.port = int(port)
        self.host = self._validate_host(host, allow_wildcard_bind)

    @staticmethod
    def _validate_host(host: str, allow_wildcard_bind: bool) -> str:
        candidate = host.strip()
        if not candidate:
            raise ValueError("host must be a non-empty IP address")
        try:
            parsed = ipaddress.ip_address(candidate)
        except ValueError as exc:
            raise ValueError("host must be a valid IPv4 or IPv6 address") from exc
        if parsed.is_unspecified and not allow_wildcard_bind:
            raise ValueError("wildcard bind addresses are disabled by default")
        return candidate

    def start_server(self) -> None:
        def run() -> None:
            sock = socket.socket()
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((self.host, self.port))
            except OSError:
                sock.close()
                return
            sock.listen()
            while True:
                conn, _ = sock.accept()
                with conn:
                    payload = conn.recv(4096)
                    if not payload:
                        continue
                    incoming = json.loads(payload.decode())
                    self.weights = [float((a + b) / 2.0) for a, b in zip(self.weights, incoming)]

        threading.Thread(target=run, daemon=True).start()

    def gossip(self, peer_ip: str) -> None:
        sock = socket.socket()
        try:
            sock.connect((peer_ip, self.port))
            sock.send(json.dumps(self.weights).encode())
        finally:
            sock.close()
