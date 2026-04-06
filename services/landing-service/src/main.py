from typing import Any

from fastapi import FastAPI

app = FastAPI(title="Landing Service")


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "landing-service"}


@app.get("/landing/{product_id}")
def landing(product_id: str) -> dict[str, Any]:
    return {
        "product_id": product_id,
        "page": f"Landing page for {product_id}",
        "headline": "Launch localized offers faster.",
        "cta": "Buy Now",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
