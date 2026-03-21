from __future__ import annotations

import numpy as np


class StrategyOptimizer:
    def __init__(self, agents: int = 3, strategy_dim: int = 2, learning_rate: float = 0.01) -> None:
        self.agents = agents
        self.learning_rate = learning_rate
        self.strategies = np.random.rand(agents, strategy_dim)

    def update(self, rewards: list[float] | np.ndarray) -> np.ndarray:
        reward_vector = np.asarray(rewards, dtype=float)
        if reward_vector.shape[0] != self.agents:
            raise ValueError("reward vector size must match number of agents")
        self.strategies += self.learning_rate * reward_vector[:, None]
        return self.strategies

    def equilibrium(self) -> np.ndarray:
        return np.mean(self.strategies, axis=0)

    def coordinate(self, rewards: list[float] | np.ndarray) -> dict[str, list[float]]:
        updated = self.update(rewards)
        return {
            "equilibrium": self.equilibrium().round(6).tolist(),
            "agent_strategies": updated.round(6).tolist(),
        }
