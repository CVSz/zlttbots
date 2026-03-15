from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeRecord:
    release_id: str
    risk_summary: str
    rollout_plan: str
    rollback_plan: str
    approver: str

    def validate(self) -> None:
        for field_name, value in self.__dict__.items():
            if not value:
                raise ValueError(f"{field_name} must be populated for high-risk change approval")


@dataclass(frozen=True)
class APIVersion:
    major: int
    minor: int
    patch: int


def assert_backward_compatible(previous: APIVersion, proposed: APIVersion, has_breaking_change: bool) -> None:
    if has_breaking_change and proposed.major <= previous.major:
        raise ValueError("Breaking API changes must increase major version")
    if not has_breaking_change and proposed.major != previous.major:
        raise ValueError("Non-breaking changes cannot alter major version")
