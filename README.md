# zTTato Platform

AI-powered Affiliate Automation Platform for product discovery, AI content generation, campaign automation, and analytics.

## Features

- AI viral video prediction
- Automated AI video generation
- Distributed GPU rendering
- Multi-marketplace product crawling
- Affiliate arbitrage detection
- Click tracking and campaign analytics
- Automation farm scheduling
- Admin dashboard
- Docker and Kubernetes deployment support

## Architecture

Crawler → AI → Video → Automation → Analytics

For details, see:

- [docs/system-overview.md](docs/system-overview.md)
- [docs/architecture.md](docs/architecture.md)

## Quick Start

```bash
./start-zttato.sh
```

## Web Dashboard

- Admin panel: http://localhost:5173

## Documentation Index

- [CHANGELOG.md](CHANGELOG.md)
- [docs/project-structure.md](docs/project-structure.md)
- [docs/installation.md](docs/installation.md)
- [docs/quick-start.md](docs/quick-start.md)
- [docs/configuration.md](docs/configuration.md)
- [docs/services/](docs/services)
- [docs/api/](docs/api)
- [docs/database/](docs/database)
- [docs/infrastructure/](docs/infrastructure)
- [docs/development/](docs/development)
- [docs/operations/](docs/operations)

## Import to GitHub

1. Create an empty GitHub repository.
2. Add remote:

```bash
git remote add origin git@github.com:<org-or-user>/zttato-platform.git
```

3. Push current branch:

```bash
git push -u origin "$(git branch --show-current)"
```

If `origin` already exists, update it:

```bash
git remote set-url origin git@github.com:<org-or-user>/zttato-platform.git
git push -u origin "$(git branch --show-current)"
```
