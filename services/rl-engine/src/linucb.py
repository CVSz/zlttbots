import numpy as np


class LinUCB:
    """Disjoint LinUCB contextual bandit with ridge regularization."""

    def __init__(self, arms: list[str], d: int, alpha: float = 1.0, lam: float = 1.0):
        if d <= 0:
            raise ValueError("d must be > 0")
        if not arms:
            raise ValueError("at least one arm is required")

        deduped_arms = list(dict.fromkeys(arms))
        self.alpha = float(alpha)
        self.lam = float(lam)
        self.d = d
        self.arms = deduped_arms
        self.A = {arm: np.eye(d, dtype=np.float64) * self.lam for arm in self.arms}
        self.b = {arm: np.zeros((d, 1), dtype=np.float64) for arm in self.arms}

    def add_arm(self, arm: str) -> None:
        if arm in self.A:
            return
        self.arms.append(arm)
        self.A[arm] = np.eye(self.d, dtype=np.float64) * self.lam
        self.b[arm] = np.zeros((self.d, 1), dtype=np.float64)

    def select(self, x: np.ndarray) -> tuple[str, float]:
        if x.shape != (self.d, 1):
            raise ValueError("x must be shaped (d, 1)")

        best_arm = self.arms[0]
        best_score = float("-inf")
        for arm in self.arms:
            a_inv = np.linalg.inv(self.A[arm])
            theta = a_inv @ self.b[arm]
            uncertainty = float(np.sqrt((x.T @ a_inv @ x).item()))
            score = float((theta.T @ x).item() + (self.alpha * uncertainty))
            if score > best_score:
                best_score = score
                best_arm = arm

        return best_arm, best_score

    def update(self, arm: str, x: np.ndarray, reward: float) -> None:
        if x.shape != (self.d, 1):
            raise ValueError("x must be shaped (d, 1)")
        if arm not in self.A:
            self.add_arm(arm)

        self.A[arm] += x @ x.T
        self.b[arm] += float(reward) * x
