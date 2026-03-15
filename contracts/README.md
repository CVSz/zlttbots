# Service API Contracts

This directory contains versioned API contracts for boundaries that must remain backward compatible.

## Rules

- Contract versions follow semantic versioning (`major.minor.patch`).
- Breaking changes must increment the major version and be approved in change management.
- CI validates each contract metadata file and fails if versions are malformed.
