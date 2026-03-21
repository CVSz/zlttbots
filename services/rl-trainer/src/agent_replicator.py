from __future__ import annotations

import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Iterable

log = logging.getLogger("rl-trainer.agent-replicator")


@dataclass(frozen=True)
class DeploymentTarget:
    host: str
    user: str = "root"
    runtime: str = "docker-compose"


class Replicator:
    def __init__(
        self,
        targets: Iterable[DeploymentTarget] | None = None,
        image: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self.targets = list(targets) if targets is not None else parse_targets(os.getenv("TARGET_NODES", ""))
        self.image = image or os.getenv("REPLICATOR_IMAGE", "zttato:latest")
        self.enabled = enabled if enabled is not None else os.getenv("REPLICATOR_ENABLED", "false").lower() == "true"

    def deploy(self, target: DeploymentTarget) -> int:
        remote_command = build_remote_command(target.runtime, self.image)
        ssh_target = f"{target.user}@{target.host}"
        cmd = ["ssh", ssh_target, remote_command]
        log.info("deploying autonomous node to %s with runtime=%s", ssh_target, target.runtime)
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            log.warning("deployment to %s failed: %s", ssh_target, completed.stderr.strip())
        return completed.returncode

    def replicate(self) -> list[dict[str, object]]:
        if not self.enabled:
            log.info("replication disabled; set REPLICATOR_ENABLED=true to enable remote deployment")
            return []

        results: list[dict[str, object]] = []
        for target in self.targets:
            code = self.deploy(target)
            results.append({"host": target.host, "runtime": target.runtime, "returncode": code})
        return results


def parse_targets(raw_targets: str) -> list[DeploymentTarget]:
    targets: list[DeploymentTarget] = []
    for raw in (item.strip() for item in raw_targets.split(",")):
        if not raw:
            continue
        runtime = "docker-compose"
        user_host = raw
        if "@" in raw:
            user, host = raw.split("@", 1)
        else:
            user, host = "root", raw
        if ":" in host:
            host, runtime = host.split(":", 1)
        targets.append(DeploymentTarget(host=host, user=user, runtime=runtime or "docker-compose"))
    return targets


def build_remote_command(runtime: str, image: str) -> str:
    quoted_image = shlex.quote(image)
    if runtime == "k8s":
        return (
            "kubectl set image deployment/zttato zttato="
            f"{quoted_image} --record && kubectl rollout status deployment/zttato"
        )
    return f"docker pull {quoted_image} && docker compose up -d"
