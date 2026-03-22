from __future__ import annotations


class ComputeTokenEngine:
    def __init__(self) -> None:
        self.stakes: dict[str, float] = {}
        self.rewards: dict[str, float] = {}

    def stake(self, worker: str, amount: float) -> float:
        self.stakes[worker] = self.stakes.get(worker, 0.0) + amount
        return self.stakes[worker]

    def reward(self, worker: str, amount: float) -> float:
        self.rewards[worker] = self.rewards.get(worker, 0.0) + amount
        return self.rewards[worker]

    def slash(self, worker: str, amount: float) -> float:
        self.stakes[worker] = max(0.0, self.stakes.get(worker, 0.0) - amount)
        return self.stakes[worker]
