import json
import logging
import os
import random
import sys
import time
from contextvars import ContextVar
from typing import Any
from uuid import uuid4

import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

SERVICE_NAME = "product-discovery"
MARKET_CRAWLER_URL = os.getenv("MARKET_CRAWLER_URL", "http://market-crawler:8000/products")
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5"))
HTTP_RETRIES = int(os.getenv("HTTP_RETRIES", "3"))
HTTP_BACKOFF = float(os.getenv("HTTP_BACKOFF", "0.5"))
REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": REQUEST_ID_CTX.get(),
        }
        if hasattr(record, "event"):
            payload["event"] = record.event
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
root_logger = logging.getLogger()
root_logger.handlers.clear()
root_logger.addHandler(handler)
root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
log = logging.getLogger(SERVICE_NAME)

app = FastAPI(title="Product Discovery")


def fetch_products() -> list[dict[str, Any]]:
    last_error: str | None = None
    for attempt in range(1, HTTP_RETRIES + 1):
        try:
            response = requests.get(MARKET_CRAWLER_URL, timeout=HTTP_TIMEOUT)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise ValueError("market-crawler response must be a JSON array")
            return payload
        except (requests.RequestException, ValueError) as exc:
            last_error = str(exc)
            log.warning(
                "market crawler request failed",
                extra={"event": {"attempt": attempt, "target": MARKET_CRAWLER_URL, "error": last_error}},
            )
            if attempt < HTTP_RETRIES:
                time.sleep(HTTP_BACKOFF * (2 ** (attempt - 1)))
    raise HTTPException(status_code=502, detail=f"market-crawler unavailable after retries: {last_error}")


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    token = REQUEST_ID_CTX.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception(
            "unhandled request error",
            extra={"event": {"method": request.method, "path": request.url.path}},
        )
        raise
    finally:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        log.info(
            "request completed",
            extra={
                "event": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": elapsed_ms,
                }
            },
        )
        REQUEST_ID_CTX.reset(token)

    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"ok": False, "detail": exc.detail})


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled application exception", extra={"event": {"error": str(exc)}})
    return JSONResponse(status_code=500, content={"ok": False, "detail": "internal server error"})


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    ok = True
    detail = "ok"
    try:
        fetch_products()
    except HTTPException as exc:
        ok = False
        detail = str(exc.detail)

    return {
        "status": "ok" if ok else "degraded",
        "service": SERVICE_NAME,
        "market_crawler_url": MARKET_CRAWLER_URL,
        "timeout": HTTP_TIMEOUT,
        "retries": HTTP_RETRIES,
        "detail": detail,
    }


@app.get("/discover")
def discover() -> dict[str, Any]:
    products = fetch_products()
    scored: list[dict[str, Any]] = []

    for product in products:
        candidate = dict(product)
        candidate["score"] = random.random()
        scored.append(candidate)

    scored.sort(key=lambda item: item["score"], reverse=True)
    top_products = scored[:10]

    log.info(
        "discovery completed",
        extra={"event": {"input_count": len(products), "selected_count": len(top_products)}},
    )
    return {"ok": True, "count": len(top_products), "items": top_products}
