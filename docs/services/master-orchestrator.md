# Master Orchestrator Service

## Purpose

The master orchestrator is the control-plane entrypoint for deployment lifecycle management and campaign operations.

## Deployment Control-Plane Endpoints

### `POST /deployments`
Creates (or reuses) a deployment request using an `idempotency_key`.

Request body:

```json
{
  "project_id": "my-app",
  "commit_sha": "a1b2c3d4",
  "environment": "production",
  "idempotency_key": "deploy-my-app-a1b2c3d4"
}
```

Behavior:
- Deterministic create: the same idempotency key always returns the same deployment record.
- Emits a `deploy.requested` decision event.

### `POST /deployments/events`
Applies a state transition event to an existing deployment.

Request body:

```json
{
  "deployment_id": "<uuid>",
  "event_type": "build.started",
  "source": "ci-worker",
  "metadata": {
    "job_id": "1234"
  }
}
```

Behavior:
- Validates transitions against the control-plane state machine.
- Rejects invalid transitions with HTTP `409`.
- Emits state transition events through the existing Kafka decision emitter.

### `GET /deployments/{deployment_id}`
Returns current deployment state and full transition history.

## State Machine

| Current State | Allowed Events | Next State |
| --- | --- | --- |
| `queued` | `build.started` | `building` |
| `building` | `build.failed`, `build.succeeded` | `failed`, `deploying` |
| `failed` | `ai.fix.started` | `fixing` |
| `fixing` | `ai.fix.applied` | `building` |
| `deploying` | `deploy.failed`, `deploy.succeeded` | `failed`, `succeeded` |
| `succeeded` | _(none)_ | terminal |

## Security and Reliability Notes

- Input is schema-validated with Pydantic.
- Idempotency key prevents duplicate deployment creation.
- State transitions are guarded and deterministic.
- Structured JSON logging is used for deployment events.
