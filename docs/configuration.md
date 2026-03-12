# Configuration

## Environment variables

Common runtime variables:

- `DB_URL`
- `REDIS_URL`
- `NODE_ENV`
- `PYTHON_ENV`
- `GPU_RENDER_ENABLED`

## Example

```env
DB_URL=postgresql://user:pass@localhost:5432/zttato
REDIS_URL=redis://localhost:6379
GPU_RENDER_ENABLED=true
```

Store sensitive values in secret stores for production deployments.
