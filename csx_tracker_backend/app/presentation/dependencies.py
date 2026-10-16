# app/presentation/dependencies.py
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.interfaces import IMarketDataProvider, IPositionRepo, IAlertObserver
from app.application.ingest_market_prices import IngestMarketPricesUseCase
from app.application.record_transaction import RecordTransactionUseCase
from app.infrastructure.repositories.postgres_repo import AsyncSessionLocal, PostgresPositionRepo
from app.infrastructure.market_providers.mef_dataef_client import MEFDataEFClient
from app.infrastructure.market_providers.csx_html_scraper import CSXHtmlScraper
from app.infrastructure.market_providers.resilient_feed import ResilientMarketFeed
from app.infrastructure.observers.telegram_observer import TelegramAlertObserver
from app.infrastructure.observers.websocket_observer import WebSocketAlertObserver


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_position_repo(session: AsyncSession = Depends(get_db_session)) -> IPositionRepo:
    return PostgresPositionRepo(session)


def get_market_provider() -> IMarketDataProvider:
    return ResilientMarketFeed(
        providers=[
            MEFDataEFClient(),
            CSXHtmlScraper(),
        ]
    )


def get_alert_observers() -> list[IAlertObserver]:
    return [
        TelegramAlertObserver(),
        WebSocketAlertObserver(),
    ]


def get_record_transaction_use_case(
    repo: IPositionRepo = Depends(get_position_repo),
) -> RecordTransactionUseCase:
    return RecordTransactionUseCase(repo=repo)


def get_ingest_market_use_case(
    provider: IMarketDataProvider = Depends(get_market_provider),
    repo: IPositionRepo = Depends(get_position_repo),
) -> IngestMarketPricesUseCase:
    return IngestMarketPricesUseCase(
        market_provider=provider,
        repo=repo,
        observers=get_alert_observers(),
    )