from __future__ import annotations

from decimal import Decimal

import pytest

from services.analytics.roi import ROIEngine
from services.core.profit_loop import ProfitLoop
from services.cost.guard import DailyCostGuard


class DummyROIRepo:
    def __init__(self, revenue: Decimal, cost: Decimal):
        self.revenue = revenue
        self.cost = cost

    def fetch_revenue(self, campaign_id: str) -> Decimal:
        return self.revenue

    def fetch_cost(self, campaign_id: str) -> Decimal:
        return self.cost


class DummyAPI:
    def __init__(self):
        self.scaled: list[tuple[str, int]] = []
        self.paused: list[str] = []

    def create_campaign(self, payload: dict[str, object]) -> str:
        return "cmp-1"

    def pause_campaign(self, campaign_id: str) -> None:
        self.paused.append(campaign_id)

    def scale_campaign(self, campaign_id: str, factor: int) -> None:
        self.scaled.append((campaign_id, factor))


def test_roi_engine_calculates_ratio_with_decimal_precision():
    engine = ROIEngine(DummyROIRepo(Decimal("120.00"), Decimal("100.00")))
    result = engine.evaluate("cmp-123")
    assert result.roi == Decimal("1.2")
    assert result.profitable is True


def test_profit_loop_scales_when_roi_reaches_threshold():
    api = DummyAPI()
    loop = ProfitLoop(ROIEngine(DummyROIRepo(Decimal("25"), Decimal("10"))), api)
    decision = loop.run_once("cmp-11")
    assert decision.action == "scale"
    assert api.scaled == [("cmp-11", 2)]


def test_profit_loop_pauses_when_roi_is_non_positive():
    api = DummyAPI()
    loop = ProfitLoop(ROIEngine(DummyROIRepo(Decimal("0"), Decimal("50"))), api)
    decision = loop.run_once("cmp-12")
    assert decision.action == "pause"
    assert api.paused == ["cmp-12"]


def test_daily_cost_guard_blocks_when_budget_exceeded():
    guard = DailyCostGuard(max_daily_cost=10.0)
    assert guard.allow(6.0) is True
    assert guard.allow(4.0) is True
    assert guard.allow(0.1) is False
    guard.reset()
    assert guard.allow(10.0) is True


def test_daily_cost_guard_rejects_negative_cost():
    guard = DailyCostGuard(max_daily_cost=10.0)
    with pytest.raises(ValueError):
        guard.allow(-1.0)
