from __future__ import annotations

from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

from orderbook import Order, OrderBook
from security import check_replay, rate_limit, verify_signature

app = FastAPI()
orderbook = OrderBook()


class OrderRequest(BaseModel):
    side: str
    price: float = Field(gt=0)
    qty: float = Field(gt=0)
    nonce: str
    message_b64: str
    signature_b64: str
    public_key_b64: str


@app.post("/order")
def place(order: OrderRequest, request: Request) -> dict[str, object]:
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit(client_ip):
        return {"error": "rate limit"}
    if not check_replay(order.nonce):
        return {"error": "replay"}
    if not verify_signature(order.message_b64, order.signature_b64, order.public_key_b64):
        return {"error": "signature"}

    placed_order = Order(order.side, order.price, order.qty)
    orderbook.add(placed_order)
    trades = orderbook.match()
    return {"order_id": placed_order.id, "trades": trades}
