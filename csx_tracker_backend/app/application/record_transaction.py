# app/application/record_transaction.py
from decimal import Decimal
from app.domain.entities import Position, ExitAlert
from app.domain.policies import BrokerFeePolicy, CSXTickPolicy
from app.domain.strategies import StrategyFactory
from app.domain.interfaces import IPositionRepo


class RecordTransactionUseCase:
    """SRP: Orchestrates portfolio ledger updates and exit alert configuration."""

    def __init__(self, repo: IPositionRepo):
        self._repo = repo

    async def record_buy(
        self, telegram_chat_id: int, ticker: str, shares: int, price_khr: int, user_id: int = 1
    ) -> tuple[Position, Decimal]:
        ticker = ticker.upper().strip()
        position = await self._repo.get_position_by_user_and_ticker(telegram_chat_id, ticker)
        if not position:
            position = Position(
                id=None,
                user_id=user_id,
                telegram_chat_id=telegram_chat_id,
                ticker=ticker,
                shares=0,
                total_cost_khr=Decimal("0"),
                fee_policy=BrokerFeePolicy(),
            )

        fee_khr = position.apply_buy(shares, price_khr)
        saved_position = await self._repo.save_position_and_transaction(
            position=position,
            side="BUY",
            shares=shares,
            price_khr=price_khr,
            fee_khr=fee_khr,
        )
        return saved_position, fee_khr

    async def record_sell(
        self, telegram_chat_id: int, ticker: str, shares: int, price_khr: int
    ) -> tuple[Position, Decimal, Decimal]:
        ticker = ticker.upper().strip()
        position = await self._repo.get_position_by_user_and_ticker(telegram_chat_id, ticker)
        if not position or position.shares <= 0:
            raise ValueError(f"No open position found for {ticker}.")

        sell_fee, realized_profit = position.apply_sell(shares, price_khr)
        saved_position = await self._repo.save_position_and_transaction(
            position=position,
            side="SELL",
            shares=shares,
            price_khr=price_khr,
            fee_khr=sell_fee,
        )
        return saved_position, sell_fee, realized_profit

    async def record_full_exit_by_position_id(
        self, position_id: int, exec_price_khr: int
    ) -> tuple[Position, Decimal]:
        position = await self._repo.get_position_by_id(position_id)
        if not position or position.shares <= 0:
            raise ValueError("Position is already closed.")

        shares_to_sell = position.shares
        sell_fee, realized_profit = position.apply_sell(shares_to_sell, exec_price_khr)
        saved_position = await self._repo.save_position_and_transaction(
            position=position,
            side="SELL",
            shares=shares_to_sell,
            price_khr=exec_price_khr,
            fee_khr=sell_fee,
        )
        return saved_position, realized_profit

    async def set_exit_alert(
        self,
        telegram_chat_id: int,
        ticker: str,
        trigger_type: str,
        target_value: Decimal,
    ) -> tuple[Position, ExitAlert]:
        ticker = ticker.upper().strip()
        position = await self._repo.get_position_by_user_and_ticker(telegram_chat_id, ticker)
        if not position or position.shares <= 0 or position.id is None:
            raise ValueError(f"No active position found for {ticker}.")

        strategy = StrategyFactory.create(trigger_type, target_value)
        exec_price_khr = strategy.compute_trigger_price_khr(position)

        alert = ExitAlert(
            id=None,
            position_id=position.id,
            trigger_type=trigger_type,
            target_value=target_value,
            target_exec_price_khr=exec_price_khr,
            is_active=True,
            strategy=strategy,
        )
        saved_alert = await self._repo.create_exit_alert(alert)
        return position, saved_alert

    async def bump_alert_target(
        self, position_id: int, bump_pct: Decimal
    ) -> tuple[Position, ExitAlert]:
        position = await self._repo.get_position_by_id(position_id)
        if not position or position.id is None:
            raise ValueError("Position not found.")

        tick = await self._repo.get_stock_tick(position.ticker)
        base_price = tick.last_price_khr if tick and tick.last_price_khr > 0 else position.executable_breakeven_khr
        new_target_khr = Decimal(CSXTickPolicy.align_up(Decimal(base_price) * (Decimal("1.0") + bump_pct)))

        strategy = StrategyFactory.create("TARGET_PRICE_KHR", new_target_khr)
        alert = ExitAlert(
            id=None,
            position_id=position.id,
            trigger_type="TARGET_PRICE_KHR",
            target_value=new_target_khr,
            target_exec_price_khr=int(new_target_khr),
            is_active=True,
            strategy=strategy,
        )
        saved_alert = await self._repo.create_exit_alert(alert)
        return position, saved_alert