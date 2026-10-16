# app/domain/entities.py
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Any
from app.domain.policies import CSXTickPolicy, BrokerFeePolicy


@dataclass(frozen=True)
class StockTick:
    """Immutable snapshot of a CSX stock's real-time market state."""
    ticker: str
    last_price_khr: int
    best_bid_khr: int = 0
    best_bid_volume: int = 0
    best_ask_khr: int = 0
    volume: int = 0
    fx_khr_usd: Decimal = Decimal("4065.00")

    @property
    def executable_exit_price_khr(self) -> int:
        """Prefers best bid price for realistic exit liquidity; falls back to last traded price."""
        return self.best_bid_khr if self.best_bid_khr > 0 else self.last_price_khr


@dataclass
class Position:
    """Aggregate Root representing a user's holding in a single CSX stock."""
    id: Optional[int]
    user_id: int
    telegram_chat_id: int
    ticker: str
    shares: int
    total_cost_khr: Decimal
    fee_policy: BrokerFeePolicy = field(default_factory=BrokerFeePolicy)
    broker_id: int = 1

    @property
    def avg_cost_per_share_khr(self) -> Decimal:
        if self.shares <= 0:
            return Decimal("0")
        return self.total_cost_khr / Decimal(self.shares)

    @property
    def executable_breakeven_khr(self) -> int:
        if self.shares <= 0:
            return 0
        raw_be = self.avg_cost_per_share_khr / (Decimal("1.0") - self.fee_policy.sell_fee_rate)
        return CSXTickPolicy.align_up(raw_be)

    def net_profit_khr_at(self, price_khr: int) -> Decimal:
        if self.shares <= 0:
            return Decimal("0")
        gross = Decimal(self.shares * price_khr)
        net_proceeds = self.fee_policy.net_sell_proceeds(gross)
        return net_proceeds - self.total_cost_khr

    def net_roi_pct_at(self, price_khr: int) -> Decimal:
        if self.total_cost_khr <= 0:
            return Decimal("0")
        return (self.net_profit_khr_at(price_khr) / self.total_cost_khr) * Decimal("100.0")

    def apply_buy(self, bought_shares: int, price_khr: int) -> Decimal:
        """Applies a buy tranche and returns the KHR fee charged."""
        gross = Decimal(bought_shares * price_khr)
        fee = self.fee_policy.calculate_buy_fee(gross)
        self.shares += bought_shares
        self.total_cost_khr += (gross + fee)
        return fee

    def apply_sell(self, sold_shares: int, price_khr: int) -> tuple[Decimal, Decimal]:
        """
        Applies a partial or full sale.
        Returns: (sell_fee_khr, realized_net_profit_khr)
        """
        if sold_shares > self.shares:
            raise ValueError(f"Cannot sell {sold_shares} shares; only holding {self.shares}.")
        allocated_cost = self.avg_cost_per_share_khr * Decimal(sold_shares)
        gross_proceeds = Decimal(sold_shares * price_khr)
        sell_fee = self.fee_policy.calculate_sell_fee(gross_proceeds)
        realized_net_profit = (gross_proceeds - sell_fee) - allocated_cost

        self.shares -= sold_shares
        self.total_cost_khr = max(Decimal("0"), self.total_cost_khr - allocated_cost)
        return sell_fee, realized_net_profit


@dataclass
class ExitAlert:
    """Domain entity linking a Position to an executable ExitTriggerStrategy."""
    id: Optional[int]
    position_id: int
    trigger_type: str  # 'TARGET_NET_ROI_PCT', 'TARGET_PRICE_KHR', 'STOP_LOSS_KHR'
    target_value: Decimal
    target_exec_price_khr: int
    is_active: bool = True
    strategy: Any = None