# Logging

Use centralized logging with structured JSON logs where possible.

Recommended: ELK or Loki stack.

## Current baseline

- Services should emit single-line JSON per event so Promtail/Loki can ingest logs without custom parsing.
- Include at least: `timestamp`, `level`, `service`, `message`, and `request_id`.
- Log upstream retry attempts separately from final failures so operators can distinguish flaky dependencies from hard outages.
- Application-level request logs should include path, method, and latency.

## Implemented example

`services/product-discovery` now emits structured JSON logs and attaches `x-request-id` to responses, which provides a reference implementation for other lightweight FastAPI services.
