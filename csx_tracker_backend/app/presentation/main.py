# app/presentation/main.py
from contextlib import asynccontextmanager
from datetime import datetime
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.repositories.postgres_repo import (
    AsyncSessionLocal,
    PostgresPositionRepo,
    init_db,
)
from app.presentation.dependencies import get_market_provider, get_alert_observers
from app.application.ingest_market_prices import IngestMarketPricesUseCase
from app.presentation.routers import portfolio_api, telegram_webhook

PHNOM_PENH_TZ = pytz.timezone("Asia/Phnom_Penh")
scheduler = AsyncIOScheduler(timezone=PHNOM_PENH_TZ)


def is_csx_trading_hours() -> bool:
    now = datetime.now(PHNOM_PENH_TZ)
    if now.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return False
    open_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    close_time = now.replace(hour=15, minute=5, second=0, microsecond=0)
    return open_time <= now <= close_time


async def scheduled_csx_ingestion_job() -> None:
    if not is_csx_trading_hours():
        return
    async with AsyncSessionLocal() as session:
        use_case = IngestMarketPricesUseCase(
            market_provider=get_market_provider(),
            repo=PostgresPositionRepo(session),
            observers=get_alert_observers(),
        )
        await use_case.execute()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler.add_job(scheduled_csx_ingestion_job, "interval", seconds=15)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="CSX Real-Time Profit & Exit Alert API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_api.router)
app.include_router(telegram_webhook.router)