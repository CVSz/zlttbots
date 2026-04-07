# Full-Stack Install + Config + Starter + Deploy Guide

This guide provides a single deterministic workflow to install, configure, start, verify, and manage the zlttbots full stack locally using Docker Compose.

## What this includes

- **Installer**: `installer/full-stack-installer.sh`
- **Config template**: `configs/env/full-stack.env.example`
- **Starter flow**: Compose build + up + health checks
- **Deploy flow**: prerequisite checks + config + startup + verification
- **Operations**: stop and uninstall commands

## 1) Prerequisites

Required commands:

- `bash`
- `docker`
- Docker Compose v2 plugin (`docker compose`) or `docker compose`
- `curl`
- `python3`
- `git`

Verify quickly:

```bash
bash installer/full-stack-installer.sh prereq
```

## 2) Configure environment

Generate a root `.env` from the secure template:

```bash
bash installer/full-stack-installer.sh config
```

Then update `.env` values before deployment.

Mandatory security changes:

- Set `DB_PASSWORD` to a strong value.
- Set `AFFILIATE_WEBHOOK_SECRET` to a strong value.
- Set `PLATFORM_API_KEY` if execution integrations are needed.

## 3) Full deployment (one command)

```bash
bash installer/full-stack-installer.sh deploy
```

The deploy command performs:

1. Host prerequisite validation
2. `.env` creation (if missing)
3. Environment security checks
4. `docker compose up -d --build --remove-orphans`
5. Critical service health probes

## 4) Starter-only mode

If `.env` already exists and is valid:

```bash
bash installer/full-stack-installer.sh starter
```

## 5) Verify stack health

```bash
bash installer/full-stack-installer.sh verify
```

Health probes include:

- `http://localhost/`
- `http://localhost:9100/healthz`
- `http://localhost:9400/healthz`
- `http://localhost:9500/healthz`
- `http://localhost:9300/healthz`

## 6) Stop or uninstall

Stop (preserve data volumes):

```bash
bash installer/full-stack-installer.sh stop
```

Stop and delete all volumes:

```bash
bash installer/full-stack-installer.sh uninstall
```

## 7) Recommended production adaptation

For production-like deployments:

- Run with dedicated secrets management (vault/external secret store).
- Keep `.env` outside source control.
- Front services with TLS-enabled ingress/reverse proxy.
- Run security scanning and tests in CI before deployment.
