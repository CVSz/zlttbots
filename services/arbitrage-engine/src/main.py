import os


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=_safe_port("ARBITRAGE_ENGINE_PORT", 9500),
    )
