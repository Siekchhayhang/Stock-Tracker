# app/application/ingest_market_prices.py
from app.domain.interfaces import IMarketDataProvider, IPositionRepo, IAlertObserver


class IngestMarketPricesUseCase:
    """
    SRP: Coordinates one market ingestion cycle:
    1. Fetch live CSX quotes
    2. Persist latest prices
    3. Broadcast live prices to WebSocket observers
    4. Evaluate active exit strategies and fire Telegram/WS alerts
    """

    def __init__(
        self,
        market_provider: IMarketDataProvider,
        repo: IPositionRepo,
        observers: list[IAlertObserver],
    ):
        self._market_provider = market_provider
        self._repo = repo
        self._observers = observers

    async def execute(self) -> dict[str, int]:
        ticks = await self._market_provider.fetch_latest_ticks()
        if not ticks:
            return {}

        await self._repo.upsert_stock_ticks(ticks)

        for observer in self._observers:
            await observer.on_prices_updated(ticks)

        for ticker, tick in ticks.items():
            holdings = await self._repo.get_active_positions_with_alerts(ticker)
            for position, alerts in holdings:
                for alert in alerts:
                    if alert.is_active and alert.strategy.is_satisfied(position, tick):
                        if alert.id is not None:
                            await self._repo.mark_alert_triggered(alert.id)
                        for observer in self._observers:
                            await observer.on_alert_triggered(position, tick, alert)

        return {t: q.last_price_khr for t, q in ticks.items()}