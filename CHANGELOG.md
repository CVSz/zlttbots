# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-03-23

### Changed

- Refined root `.gitignore` to cover Python/Node caches, local temp output, and report artifacts while preserving `.env.example` tracking.
- Updated the root agent governance specification to include final output and conflict-resolution directives.
- Updated README operational guidance, support links, and license alignment for easier onboarding.
- Replaced the placeholder security policy template with a concrete reporting and response process.
- Standardized repository legal and support metadata in root documentation files.

## [2.0.0] - 2026-03-12

### Changed

- Upgraded all Node.js service package versions to `2.0.0` for a unified final release.
- Upgraded Node.js runtime images from `node:20` to `node:22` across service Dockerfiles.
- Upgraded Playwright base images from `v1.43.0-jammy` to `v1.55.0-jammy` for automation services.
- Upgraded Python service runtime images from `python:3.11` to `python:3.12`.
- Upgraded CUDA runtime image for GPU renderer to `12.6.3`.
- Pinned and upgraded Python dependencies to current stable versions for reproducible builds.
- Upgraded core infrastructure images in compose: PostgreSQL `17`, Redis `7.4`.

## [1.0.0] - 2026-03-13

### Added

- Viral video prediction service
- AI video generator service
- GPU distributed renderer
- Multi-marketplace crawler foundation
- Affiliate arbitrage engine
- Click tracking service
- Analytics backend
- React admin panel
- Automation farm orchestration
- PostgreSQL schema and migrations
- Kubernetes deployment manifests
- CI/CD automation scripts
- Full repository documentation set under `docs/`

### Infrastructure

- Docker Compose orchestration
- Redis queue integration
- PostgreSQL service configuration
- Worker startup and supervisor scripts

### Security

- Environment-based configuration support
- Operational guidance for secrets handling

## [0.9.0]

### Added

- Initial project architecture
- Early crawler prototype
- Database schema draft

## [0.1.0]

### Initial

- Project initialization
