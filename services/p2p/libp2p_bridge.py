from __future__ import annotations

import os
import subprocess

BIN = os.getenv("LIBP2P_BIN", "/usr/local/bin/libp2p-node")



def start() -> subprocess.Popen:
    return subprocess.Popen([BIN, "--port", "9100"])


if __name__ == "__main__":
    start().wait()
