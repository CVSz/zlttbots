from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger("deployment-controller")


class DeploymentState(str, Enum):
    queued = "queued"
    building = "building"
    failed = "failed"
    fixing = "fixing"
    deploying = "deploying"
    succeeded = "succeeded"


ALLOWED_TRANSITIONS: dict[DeploymentState, dict[str, DeploymentState]] = {
    DeploymentState.queued: {
        "build.started": DeploymentState.building,
    },
    DeploymentState.building: {
        "build.failed": DeploymentState.failed,
        "build.succeeded": DeploymentState.deploying,
    },
    DeploymentState.failed: {
        "ai.fix.started": DeploymentState.fixing,
    },
    DeploymentState.fixing: {
        "ai.fix.applied": DeploymentState.building,
    },
    DeploymentState.deploying: {
        "deploy.failed": DeploymentState.failed,
        "deploy.succeeded": DeploymentState.succeeded,
    },
    DeploymentState.succeeded: {},
}


class DeploymentCreateRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=120)
    commit_sha: str = Field(min_length=7, max_length=64)
    environment: str = Field(default="production", min_length=2, max_length=32)
    idempotency_key: str = Field(min_length=8, max_length=120)


class DeploymentEventRequest(BaseModel):
    deployment_id: str = Field(min_length=1)
    event_type: str = Field(min_length=3, max_length=64)
    source: str = Field(default="system", min_length=2, max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeploymentRecord(BaseModel):
    deployment_id: str
    project_id: str
    commit_sha: str
    environment: str
    state: DeploymentState
    created_at: str
    updated_at: str
    history: list[dict[str, Any]] = Field(default_factory=list)


@dataclass
class DeploymentStore:
    _deployments: dict[str, DeploymentRecord] = field(default_factory=dict)
    _idempotency_index: dict[str, str] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def create(self, payload: DeploymentCreateRequest) -> DeploymentRecord:
        with self._lock:
            if payload.idempotency_key in self._idempotency_index:
                deployment_id = self._idempotency_index[payload.idempotency_key]
                return self._deployments[deployment_id]

            deployment_id = str(uuid4())
            timestamp = self._now_iso()
            record = DeploymentRecord(
                deployment_id=deployment_id,
                project_id=payload.project_id,
                commit_sha=payload.commit_sha,
                environment=payload.environment.lower(),
                state=DeploymentState.queued,
                created_at=timestamp,
                updated_at=timestamp,
                history=[
                    {
                        "event_type": "deployment.created",
                        "source": "platform-core",
                        "timestamp": timestamp,
                        "metadata": {
                            "project_id": payload.project_id,
                            "commit_sha": payload.commit_sha,
                            "environment": payload.environment.lower(),
                        },
                    }
                ],
            )
            self._deployments[deployment_id] = record
            self._idempotency_index[payload.idempotency_key] = deployment_id
            self._log("deployment.created", deployment_id, {"state": record.state})
            return record

    def apply_event(self, payload: DeploymentEventRequest) -> DeploymentRecord:
        with self._lock:
            if payload.deployment_id not in self._deployments:
                raise KeyError("deployment not found")

            record = self._deployments[payload.deployment_id]
            allowed = ALLOWED_TRANSITIONS.get(record.state, {})
            if payload.event_type not in allowed:
                raise ValueError(
                    f"event {payload.event_type} is invalid when deployment is in state {record.state}"
                )

            next_state = allowed[payload.event_type]
            timestamp = self._now_iso()
            record.state = next_state
            record.updated_at = timestamp
            record.history.append(
                {
                    "event_type": payload.event_type,
                    "source": payload.source,
                    "timestamp": timestamp,
                    "metadata": payload.metadata,
                    "next_state": next_state,
                }
            )
            self._log(payload.event_type, payload.deployment_id, {"next_state": next_state})
            return record

    def get(self, deployment_id: str) -> DeploymentRecord:
        with self._lock:
            if deployment_id not in self._deployments:
                raise KeyError("deployment not found")
            return self._deployments[deployment_id]

    def _log(self, event_type: str, deployment_id: str, context: dict[str, Any]) -> None:
        message = {
            "event_type": event_type,
            "deployment_id": deployment_id,
            "context": context,
            "timestamp": self._now_iso(),
        }
        logger.info(json.dumps(message, sort_keys=True))
