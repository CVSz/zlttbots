import os

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=int(os.getenv("ARBITRAGE_ENGINE_PORT", "9500")),
    )
