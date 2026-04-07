# Singularity Autonomous Cybersecurity System

This service implements an event-driven, deterministic security remediation loop:

`Sense -> Analyze -> Plan -> Act -> Verify -> Learn -> Enforce`

## Components

- `src/orchestrator.py`: FIFO event bus and orchestrator dispatch loop.
- `src/agents.py`: Scan, reasoning, remediation, attack simulation, verification, defense, PR recommendation, and learning agents.
- `src/verify.py`: SSRF and path traversal verification probes.
- `src/risk.py`: risk scoring function.
- `policy/`: OPA, Kyverno, and Falco policy templates.

## Local run

```bash
python3 services/singularity/src/run.py --sarif /path/to/merged.sarif
```
