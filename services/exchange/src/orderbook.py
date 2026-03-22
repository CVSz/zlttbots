from __future__ import annotations

import heapq
import time
from dataclasses import dataclass, field


@dataclass(order=False)
class Order:
    side: str
    price: float
    qty: float
    oid: str | None = None
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        if self.price <= 0 or self.qty <= 0:
            raise ValueError("price and qty must be positive")
        self.id = self.oid or f"{self.side}-{self.ts:.6f}"


class OrderBook:
    def __init__(self) -> None:
        self.buys: list[tuple[float, float, Order]] = []
        self.sells: list[tuple[float, float, Order]] = []

    def add(self, order: Order) -> None:
        if order.side == "buy":
            heapq.heappush(self.buys, (-order.price, order.ts, order))
            return
        heapq.heappush(self.sells, (order.price, order.ts, order))

    def match(self) -> list[dict[str, float | str]]:
        trades: list[dict[str, float | str]] = []
        while self.buys and self.sells:
            best_buy_price, _, buy = self.buys[0]
            best_sell_price, _, sell = self.sells[0]
            if -best_buy_price < best_sell_price:
                break

            qty = min(buy.qty, sell.qty)
            trades.append(
                {
                    "buy_order_id": buy.id,
                    "sell_order_id": sell.id,
                    "price": float(best_sell_price),
                    "qty": float(qty),
                }
            )
            buy.qty -= qty
            sell.qty -= qty
            if buy.qty == 0:
                heapq.heappop(self.buys)
            if sell.qty == 0:
                heapq.heappop(self.sells)
        return trades
