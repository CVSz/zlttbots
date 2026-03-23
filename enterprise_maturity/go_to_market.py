from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


@dataclass(frozen=True)
class DailyKPI:
    users_target_min: int
    users_target_max: int
    deploys_target_min: int
    shares_trend_required: bool

    def validate(self) -> None:
        if self.users_target_min <= 0 or self.users_target_max <= 0:
            raise ValueError("User targets must be positive")
        if self.users_target_min > self.users_target_max:
            raise ValueError("Minimum user target must be <= maximum target")
        if self.deploys_target_min <= 0:
            raise ValueError("Deploy target must be positive")


@dataclass(frozen=True)
class ExecutionBlock:
    name: str
    tasks: tuple[str, ...]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Execution block name is required")
        if not self.tasks:
            raise ValueError(f"Execution block '{self.name}' must include tasks")


@dataclass(frozen=True)
class DailyExecutionPlan:
    day: int
    objective: str
    blocks: tuple[ExecutionBlock, ...]
    kpi: DailyKPI

    def validate(self) -> None:
        if self.day < 1:
            raise ValueError("Day must be >= 1")
        if not self.objective.strip():
            raise ValueError("Objective is required")
        if not self.blocks:
            raise ValueError("At least one execution block is required")
        for block in self.blocks:
            block.validate()
        self.kpi.validate()


@dataclass(frozen=True)
class ContentInput:
    product_link: str
    social_proof_count: int

    def validate(self) -> None:
        if not self.product_link.startswith("http"):
            raise ValueError("Product link must be an absolute URL")
        if self.social_proof_count < 0:
            raise ValueError("Social proof count must be >= 0")


@dataclass(frozen=True)
class DeckMetrics:
    users: int
    deploys: int
    daily_growth_percent: float

    def validate(self) -> None:
        if self.users < 0 or self.deploys < 0:
            raise ValueError("Users and deploys must be >= 0")
        if self.daily_growth_percent < 0:
            raise ValueError("Daily growth percent must be >= 0")


HOOKS: tuple[str, ...] = (
    "This feels illegal.",
    "AI just replaced this workflow.",
    "DevOps just changed.",
)


def _select_hook(slot: int) -> str:
    if slot < 0:
        raise ValueError("slot must be >= 0")
    return HOOKS[slot % len(HOOKS)]


def generate_daily_plan(day: int) -> DailyExecutionPlan:
    if day < 1:
        raise ValueError("day must be >= 1")

    if day <= 3:
        objective = "Launch burst: reach first 50-100 users"
    elif day <= 7:
        objective = "Traction loop: scale to 200-300 users"
    else:
        objective = "Scale phase: work toward 1,000 users"

    plan = DailyExecutionPlan(
        day=day,
        objective=objective,
        blocks=(
            ExecutionBlock(
                name="Morning",
                tasks=(
                    "Test signup-to-deploy flow",
                    "Fix at least one product bug",
                    "Improve one UX friction point",
                    "Review users, deploys, and failures",
                ),
            ),
            ExecutionBlock(
                name="Midday",
                tasks=(
                    "Publish 3 posts (Twitter, Reddit, TikTok)",
                    "Send 20 direct outreach messages to developers",
                ),
            ),
            ExecutionBlock(
                name="Evening",
                tasks=(
                    "Improve AI-fix visibility in product flow",
                    "Reply to all inbound user messages",
                    "Collect feedback from at least 3 users",
                ),
            ),
        ),
        kpi=DailyKPI(
            users_target_min=50,
            users_target_max=100,
            deploys_target_min=100,
            shares_trend_required=True,
        ),
    )
    plan.validate()
    return plan


def generate_post(content: ContentInput, slot: int) -> str:
    content.validate()
    hook = _select_hook(slot)
    social_proof_line = (
        f"{content.social_proof_count}+ developers already testing this."
        if content.social_proof_count > 0
        else "Looking for early testers."
    )
    return (
        f"{hook}\n\n"
        "❌ Build failed\n"
        "🤖 AI analyzed logs and fixed the issue\n"
        "✅ Deploy succeeded\n\n"
        f"{social_proof_line}\n"
        f"Try it: {content.product_link}"
    )


def generate_pitch_deck_outline(metrics: DeckMetrics) -> Sequence[str]:
    metrics.validate()
    return (
        "Problem: Deployments are complex and failure-prone.",
        "Solution: One-click deployment with AI-assisted auto-fix.",
        "Demo: Build failure -> AI diagnosis -> successful deployment.",
        "Market: DevOps and cloud tooling is a large and expanding segment.",
        "Product: CI/CD, AI auto-fix, live logs, Git-based deploys.",
        f"Traction: Users={metrics.users}, Deploys={metrics.deploys}, Daily growth={metrics.daily_growth_percent:.1f}%.",
        "Business model: SaaS subscriptions, team plans, enterprise contracts.",
        "Competition: Vercel/Render and cloud vendors; differentiated by self-healing AI workflows.",
        "Vision: Fully autonomous DevOps operations powered by AI.",
        "Ask: Raise capital to scale product quality and distribution.",
    )


def generate_date_stamped_status(current_day: date, metrics: DeckMetrics) -> str:
    metrics.validate()
    return (
        f"Status as of {current_day.isoformat()}: "
        f"users={metrics.users}, deploys={metrics.deploys}, daily_growth={metrics.daily_growth_percent:.1f}%"
    )
