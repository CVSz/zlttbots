from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SpendControlPlane:
    global_daily_cap: float
    roi_stop_threshold: float
    per_campaign_caps: dict[str, float]
    anomaly_multiplier: float = 2.5
    kill_switch_enabled: bool = False

    def enable_kill_switch(self) -> None:
        self.kill_switch_enabled = True

    def disable_kill_switch(self) -> None:
        self.kill_switch_enabled = False

    def allow_spend(self, campaign_id: str, spend: float, campaign_spent_today: float, global_spent_today: float) -> bool:
        if spend < 0:
            raise ValueError("spend must be non-negative")
        if self.kill_switch_enabled:
            return False

        campaign_cap = self.per_campaign_caps.get(campaign_id)
        if campaign_cap is not None and (campaign_spent_today + spend) > campaign_cap:
            return False

        return (global_spent_today + spend) <= self.global_daily_cap

    def should_stop_for_roi(self, roi: float) -> bool:
        return roi < self.roi_stop_threshold

    def is_cost_spike(self, baseline_spend: float, new_spend: float) -> bool:
        if baseline_spend <= 0:
            return False
        return new_spend >= (baseline_spend * self.anomaly_multiplier)
