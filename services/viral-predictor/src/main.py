import os



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=int(os.getenv("VIRAL_PREDICTOR_PORT", "9100")),
    )
