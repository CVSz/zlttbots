# Privileged Action Audit Event Schema

All privileged operations in admin and internal APIs must emit immutable audit events.

## Required fields

- `event_id`: globally unique ID
- `timestamp`: RFC3339 UTC timestamp
- `actor.id`: principal identifier
- `actor.type`: `user` or `service`
- `actor.roles`: resolved RBAC roles at action time
- `action`: canonical verb (`create`, `update`, `delete`, `approve`, etc.)
- `resource.type`: target entity type
- `resource.id`: target entity ID
- `source.ip`: source address
- `request_id`: trace correlation ID
- `result`: `success` or `failure`
- `error_code`: populated when `result=failure`

## Storage requirements

- Append-only sink.
- Minimum 1 year retention for privileged events.
- Queryable by actor, resource, request_id, and time range.
