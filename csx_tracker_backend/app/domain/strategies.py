# app/domain/strategies.py
from decimal import Decimal
from typing import Protocol
from app.domain.entities import Position, StockTick
from app.domain.policies import CSXTickPolicy


class ExitTriggerStrategy(Protocol):
    """Contract for all CSX exit trigger algorithms."""
    def compute_trigger_price_khr(self, position: Position) -> int:
        ...

    def is_satisfied(self, position: Position, tick: StockTick) -> bool:
        ...


class TargetNetRoiStrategy:
    """Triggers when executable price yields >= target_roi_pct net of both buy and sell fees."""
    def __init__(self, target_roi_pct: Decimal):
        self.target_roi_pct = target_roi_pct  # e.g. Decimal("12.0") for +12%

    def compute_trigger_price_khr(self, position: Position) -> int:
        if position.shares <= 0:
            return 0
        roi_multiplier = Decimal("1.0") + (self.target_roi_pct / Decimal("100.0"))
        raw_target = (position.avg_cost_per_share_khr * roi_multiplier) / (
            Decimal("1.0") - position.fee_policy.sell_fee_rate
        )
        return CSXTickPolicy.align_up(raw_target)

    def is_satisfied(self, position: Position, tick: StockTick) -> bool:
        target_khr = self.compute_trigger_price_khr(position)
        return target_khr > 0 and tick.executable_exit_price_khr >= target_khr


class TargetPriceStrategy:
    """Triggers when executable price reaches or exceeds a fixed KHR price."""
    def __init__(self, target_price_khr: Decimal):
        self.target_price_khr = CSXTickPolicy.align_up(target_price_khr)

    def compute_trigger_price_khr(self, position: Position) -> int:
        return self.target_price_khr

    def is_satisfied(self, position: Position, tick: StockTick) -> bool:
        return tick.executable_exit_price_khr >= self.target_price_khr


class StopLossStrategy:
    """Triggers when last traded price falls to or below a protective floor in KHR."""
    def __init__(self, stop_price_khr: Decimal):
        self.stop_price_khr = CSXTickPolicy.align_down(stop_price_khr)

    def compute_trigger_price_khr(self, position: Position) -> int:
        return self.stop_price_khr

    def is_satisfied(self, position: Position, tick: StockTick) -> bool:
        return 0 < tick.last_price_khr <= self.stop_price_khr


class StrategyFactory:
    """Factory that hydrates the proper strategy instance from database rows."""
    @staticmethod
    def create(trigger_type: str, target_value: Decimal) -> ExitTriggerStrategy:
        if trigger_type == "TARGET_NET_ROI_PCT":
            return TargetNetRoiStrategy(target_value)
        if trigger_type == "TARGET_PRICE_KHR":
            return TargetPriceStrategy(target_value)
        if trigger_type == "STOP_LOSS_KHR":
            return StopLossStrategy(target_value)
        raise ValueError(f"Unsupported trigger_type: {trigger_type}")