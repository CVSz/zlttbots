from __future__ import annotations

from typing import Any


def train_distributed_ppo(env: str = "CartPole-v1", num_rollout_workers: int = 2) -> dict[str, Any]:
    """Run a single distributed PPO training iteration via Ray RLlib.

    Ray is imported lazily so the module remains importable in environments
    where the optional distributed stack is not installed.
    """
    import ray
    from ray.rllib.algorithms.ppo import PPOConfig

    ray.init(address="auto", ignore_reinit_error=True)
    config = (
        PPOConfig()
        .environment(env=env)
        .rollouts(num_rollout_workers=num_rollout_workers)
        .training(model={"fcnet_hiddens": [64, 64]})
    )
    algo = config.build()
    return algo.train()
