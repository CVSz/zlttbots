from __future__ import annotations

import json
import socket
import threading
from typing import Iterable


class P2PAgent:
    def __init__(self, weights: Iterable[float], port: int = 9000, host: str = "127.0.0.1") -> None:
        self.weights = [float(value) for value in weights]
        self.port = int(port)
        self.host = host

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
