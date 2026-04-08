import os

SERVICE_HOST = os.getenv("SERVICE_HOST", "127.0.0.1")


def _safe_port(env_key: str, default: int) -> int:
    raw = os.getenv(env_key)
    if raw is None:
        return default
    value = raw.strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    if parsed <= 0 or parsed > 65535:
        return default
    return parsed


SERVICE_PORT = _safe_port("VIRAL_PREDICTOR_PORT", 9100)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
    )
