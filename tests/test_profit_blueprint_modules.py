from __future__ import annotations

from decimal import Decimal

import pytest

from services.analytics.roi import ROIEngine
from services.analytics.unit_economics import UnitEconomics
from services.core.profit_loop import ProfitLoop
from services.cost.guard import DailyCostGuard
from services.cost.controls import SpendControlPlane
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


class LossEconomicsProvider:
    def snapshot(self, campaign_id: str) -> UnitEconomics:
        return UnitEconomics(
            campaign_id=campaign_id,
            revenue=Decimal("10"),
            cost=Decimal("25"),
            acquisitions=2,
            active_customers=2,
        )


def test_roi_engine_calculates_ratio_with_decimal_precision():
    engine = ROIEngine(DummyROIRepo(Decimal("120.00"), Decimal("100.00")))
    result = engine.evaluate("cmp-123")
    assert result.roi == Decimal("1.2")
    assert result.profitable is True


def test_unit_economics_computes_profit_cpa_ltv_and_roas():
    snapshot = UnitEconomics(
        campaign_id="cmp-ue",
        revenue=Decimal("120"),
        cost=Decimal("60"),
        acquisitions=3,
        active_customers=4,
    )
    assert snapshot.profit == Decimal("60")
    assert snapshot.cpa == Decimal("20")
    assert snapshot.ltv == Decimal("30")
    assert snapshot.roas == Decimal("2")


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


def test_profit_loop_enforces_stop_loss_from_unit_economics():
    api = DummyAPI()
    loop = ProfitLoop(
        ROIEngine(DummyROIRepo(Decimal("100"), Decimal("10"))),
        api,
        economics_provider=LossEconomicsProvider(),
    )
    decision = loop.run_once("cmp-loss")
    assert decision.action == "stop_loss"
    assert api.paused == ["cmp-loss"]


def test_profit_loop_respects_global_kill_switch(monkeypatch):
    monkeypatch.setenv("PROFIT_GLOBAL_KILL_SWITCH", "true")
    api = DummyAPI()
    loop = ProfitLoop(ROIEngine(DummyROIRepo(Decimal("100"), Decimal("10"))), api)
    decision = loop.run_once("cmp-any")
    assert decision.action == "halt"


def test_spend_control_plane_validates_caps_and_anomaly_and_roi():
    control = SpendControlPlane(
        global_daily_cap=100.0,
        roi_stop_threshold=1.0,
        per_campaign_caps={"cmp-1": 30.0},
    )
    assert control.allow_spend("cmp-1", spend=10.0, campaign_spent_today=5.0, global_spent_today=20.0) is True
    assert control.allow_spend("cmp-1", spend=26.0, campaign_spent_today=5.0, global_spent_today=20.0) is False
    assert control.should_stop_for_roi(0.8) is True
    assert control.is_cost_spike(baseline_spend=10.0, new_spend=30.0) is True
