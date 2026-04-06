import os

SERVICE_HOST = os.getenv("SERVICE_HOST", "127.0.0.1")
SERVICE_PORT = int(os.getenv("VIRAL_PREDICTOR_PORT", "9100"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
    )
