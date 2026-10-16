# app/domain/policies.py
import math
from dataclasses import dataclass
from decimal import Decimal


class CSXTickPolicy:
    """SRP: Solely responsible for official CSX KHR price-step rules."""

    @staticmethod
    def get_tick_size(price_khr: float | Decimal) -> int:
        p = float(price_khr)
        if p < 10_000:
            return 10
        if p < 50_000:
            return 20
        if p < 100_000:
            return 50
        if p < 200_000:
            return 100
        if p < 400_000:
            return 500
        return 1_000

    @classmethod
    def align_up(cls, raw_price_khr: Decimal | float) -> int:
        """Rounds UP to the nearest valid CSX limit-order tick."""
        if raw_price_khr <= 0:
            return 0
        tick = cls.get_tick_size(raw_price_khr)
        return int(math.ceil(float(raw_price_khr) / tick) * tick)

    @classmethod
    def align_down(cls, raw_price_khr: Decimal | float) -> int:
        """Rounds DOWN to the nearest valid CSX limit-order tick."""
        if raw_price_khr <= 0:
            return 0
        tick = cls.get_tick_size(raw_price_khr)
        return int(math.floor(float(raw_price_khr) / tick) * tick)


@dataclass(frozen=True)
class BrokerFeePolicy:
    """SRP: Encapsulates all-in CSX regulatory + broker commission math."""
    buy_fee_rate: Decimal = Decimal("0.0050")   # Default 0.50% all-in
    sell_fee_rate: Decimal = Decimal("0.0050")  # Default 0.50% all-in
    min_fee_khr: Decimal = Decimal("0")

    def calculate_buy_fee(self, gross_khr: Decimal) -> Decimal:
        return max(gross_khr * self.buy_fee_rate, self.min_fee_khr)

    def calculate_sell_fee(self, gross_khr: Decimal) -> Decimal:
        return max(gross_khr * self.sell_fee_rate, self.min_fee_khr)

    def net_sell_proceeds(self, gross_khr: Decimal) -> Decimal:
        return gross_khr - self.calculate_sell_fee(gross_khr)