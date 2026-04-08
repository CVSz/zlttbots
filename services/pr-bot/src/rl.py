from __future__ import annotations

from dataclasses import dataclass


Category = str


@dataclass(frozen=True)
class Feedback:
    repo: str
    accepted: bool
    severity: str
    category: Category


class ReviewerBandit:
    def __init__(self) -> None:
        self._weights: dict[Category, float] = {
            "security": 1.0,
            "perf": 1.0,
            "quality": 1.0,
        }

    def select_agents(self) -> list[str]:
        return [
            category
            for category, _ in sorted(self._weights.items(), key=lambda entry: (-entry[1], entry[0]))
        ]

    def update(self, feedback: Feedback) -> None:
        if feedback.category not in self._weights:
            return
        delta = 0.1 if feedback.accepted else -0.1
        updated = self._weights[feedback.category] + delta
        self._weights[feedback.category] = max(0.0, round(updated, 4))

    def snapshot(self) -> dict[str, float]:
        return dict(self._weights)
