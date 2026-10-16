# app/domain/interfaces.py
from decimal import Decimal
from typing import Protocol, Optional
from app.domain.entities import StockTick, Position, ExitAlert


class IMarketDataProvider(Protocol):
    async def fetch_latest_ticks(self) -> dict[str, StockTick]:
        """Returns a mapping of ticker -> StockTick."""
        ...


class IPositionRepo(Protocol):
    async def upsert_stock_ticks(self, ticks: dict[str, StockTick]) -> None:
        ...

    async def get_stock_tick(self, ticker: str) -> Optional[StockTick]:
        ...

    async def get_position_by_user_and_ticker(
        self, telegram_chat_id: int, ticker: str
    ) -> Optional[Position]:
        ...

    async def get_position_by_id(self, position_id: int) -> Optional[Position]:
        ...

    async def get_user_portfolio(
        self, telegram_chat_id: int
    ) -> list[tuple[Position, StockTick, list[ExitAlert]]]:
        ...

    async def get_active_positions_with_alerts(
        self, ticker: str
    ) -> list[tuple[Position, list[ExitAlert]]]:
        ...

    async def save_position_and_transaction(
        self, position: Position, side: str, shares: int, price_khr: int, fee_khr: Decimal
    ) -> Position:
        ...

    async def create_exit_alert(self, alert: ExitAlert) -> ExitAlert:
        ...

    async def mark_alert_triggered(self, alert_id: int) -> None:
        ...


class IAlertObserver(Protocol):
    async def on_prices_updated(self, ticks: dict[str, StockTick]) -> None:
        ...

    async def on_alert_triggered(
        self, position: Position, tick: StockTick, alert: ExitAlert
    ) -> None:
        ...