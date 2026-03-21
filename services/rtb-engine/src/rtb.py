from __future__ import annotations


class RTBEngine:
    def __init__(self, base_bid: float = 1.0, min_bid: float = 0.01) -> None:
        self.base_bid = base_bid
        self.min_bid = min_bid

    def compute_bid(self, ctr: float, cvr: float, value: float = 1.0) -> float:
        expected_value = max(ctr, 0.0) * max(cvr, 0.0) * max(value, 0.0)
        bid = self.base_bid * expected_value
        return float(max(bid, self.min_bid))
