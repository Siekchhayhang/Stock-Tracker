# app/infrastructure/market_providers/resilient_feed.py
import logging
from app.domain.entities import StockTick
from app.domain.interfaces import IMarketDataProvider

logger = logging.getLogger(__name__)


class ResilientMarketFeed:
    """Iterates through configured providers in order until valid CSX quotes are returned."""

    def __init__(self, providers: list[IMarketDataProvider]):
        self._providers = providers

    async def fetch_latest_ticks(self) -> dict[str, StockTick]:
        for provider in self._providers:
            try:
                ticks = await provider.fetch_latest_ticks()
                if ticks:
                    return ticks
            except Exception as exc:
                logger.warning(
                    "Market provider %s failed (%s); falling back to next provider.",
                    provider.__class__.__name__,
                    exc,
                )
        return {}