# Configuration

This file summarizes configuration sources and environment conventions.

## Configuration sources

- Runtime environment files (for example `configs/env/production.env`)
- Docker Compose service environment declarations
- Reverse-proxy routing in `configs/nginx.conf`

## Common environment variables

- `DB_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `NODE_ENV`: Node.js runtime mode
- `PYTHON_ENV`: Python runtime mode
- `GPU_RENDER_ENABLED`: feature toggle for GPU rendering paths

## Example

```env
DB_URL=postgresql://user:pass@localhost:5432/zttato
REDIS_URL=redis://localhost:6379
NODE_ENV=production
PYTHON_ENV=production
GPU_RENDER_ENABLED=true
```

## Configuration practices

- Keep secrets out of source control.
- Use per-environment `.env` variants with explicit ownership.
- Validate critical values (DB/Redis URLs, service credentials) before deploy.
- Rotate sensitive values after incident response or credential exposure.
