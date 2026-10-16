# app/infrastructure/repositories/postgres_repo.py
import os
from decimal import Decimal
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.domain.entities import StockTick, Position, ExitAlert
from app.domain.policies import BrokerFeePolicy
from app.domain.strategies import StrategyFactory

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/csx_tracker"
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Automatically creates tables and seeds default CSX broker profile (id=1) on startup."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS broker_profiles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                buy_fee_rate NUMERIC(6, 5) NOT NULL DEFAULT 0.00500,
                sell_fee_rate NUMERIC(6, 5) NOT NULL DEFAULT 0.00500,
                min_fee_khr BIGINT NOT NULL DEFAULT 0
            );
        """))
        await conn.execute(text("""
            INSERT INTO broker_profiles (id, name, buy_fee_rate, sell_fee_rate, min_fee_khr)
            VALUES (1, 'Default CSX Broker (0.50%)', 0.00500, 0.00500, 0)
            ON CONFLICT (id) DO NOTHING;
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks (
                ticker VARCHAR(10) PRIMARY KEY,
                company_name VARCHAR(150) NOT NULL,
                board VARCHAR(20) DEFAULT 'MAIN',
                last_price_khr BIGINT NOT NULL DEFAULT 0,
                base_price_khr BIGINT NOT NULL DEFAULT 0,
                best_bid_khr BIGINT DEFAULT 0,
                best_bid_volume BIGINT DEFAULT 0,
                daily_fx_khr_usd NUMERIC(8, 2) DEFAULT 4065.00,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                telegram_chat_id BIGINT NOT NULL,
                ticker VARCHAR(10) REFERENCES stocks(ticker),
                broker_id INT REFERENCES broker_profiles(id) DEFAULT 1,
                total_shares BIGINT NOT NULL DEFAULT 0,
                total_cost_khr NUMERIC(18, 2) NOT NULL DEFAULT 0,
                avg_cost_per_share_khr NUMERIC(14, 2) NOT NULL DEFAULT 0,
                breakeven_price_khr BIGINT NOT NULL DEFAULT 0,
                UNIQUE(user_id, ticker, broker_id)
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                position_id INT REFERENCES positions(id) ON DELETE CASCADE,
                side VARCHAR(4) CHECK (side IN ('BUY', 'SELL')),
                shares BIGINT NOT NULL CHECK (shares > 0),
                price_khr BIGINT NOT NULL CHECK (price_khr > 0),
                fee_khr NUMERIC(14, 2) NOT NULL,
                executed_at TIMESTAMPTZ DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS exit_alerts (
                id SERIAL PRIMARY KEY,
                position_id INT REFERENCES positions(id) ON DELETE CASCADE,
                trigger_type VARCHAR(25) NOT NULL,
                target_value NUMERIC(14, 2) NOT NULL,
                target_exec_price_khr BIGINT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                last_triggered_at TIMESTAMPTZ
            );
        """))


class PostgresPositionRepo:
    """SQLAlchemy 2.0 Async implementation of IPositionRepo."""

    def __init__(self, session: AsyncSession):
        self._db = session

    async def upsert_stock_ticks(self, ticks: dict[str, StockTick]) -> None:
        for ticker, tick in ticks.items():
            await self._db.execute(
                text("""
                    INSERT INTO stocks (ticker, company_name, last_price_khr, best_bid_khr, best_bid_volume, daily_fx_khr_usd, updated_at)
                    VALUES (:ticker, :ticker, :last_p, :bid_p, :bid_v, :fx, NOW())
                    ON CONFLICT (ticker) DO UPDATE SET
                        last_price_khr = EXCLUDED.last_price_khr,
                        best_bid_khr = EXCLUDED.best_bid_khr,
                        best_bid_volume = EXCLUDED.best_bid_volume,
                        daily_fx_khr_usd = EXCLUDED.daily_fx_khr_usd,
                        updated_at = NOW()
                """),
                {
                    "ticker": ticker,
                    "last_p": tick.last_price_khr,
                    "bid_p": tick.best_bid_khr,
                    "bid_v": tick.best_bid_volume,
                    "fx": tick.fx_khr_usd,
                },
            )
        await self._db.commit()

    async def get_stock_tick(self, ticker: str) -> Optional[StockTick]:
        res = await self._db.execute(
            text("""
                SELECT ticker, last_price_khr, best_bid_khr, best_bid_volume, daily_fx_khr_usd
                FROM stocks WHERE ticker = :t
            """),
            {"t": ticker.upper()},
        )
        row = res.mappings().first()
        if not row:
            return None
        return StockTick(
            ticker=row["ticker"],
            last_price_khr=row["last_price_khr"],
            best_bid_khr=row["best_bid_khr"] or row["last_price_khr"],
            best_bid_volume=row["best_bid_volume"] or 0,
            fx_khr_usd=row["daily_fx_khr_usd"],
        )

    def _map_position(self, row: dict) -> Position:
        return Position(
            id=row["id"],
            user_id=row["user_id"],
            telegram_chat_id=row["telegram_chat_id"],
            ticker=row["ticker"],
            shares=row["total_shares"],
            total_cost_khr=Decimal(str(row["total_cost_khr"])),
            broker_id=row["broker_id"],
            fee_policy=BrokerFeePolicy(
                buy_fee_rate=Decimal(str(row["buy_fee_rate"])),
                sell_fee_rate=Decimal(str(row["sell_fee_rate"])),
                min_fee_khr=Decimal(str(row["min_fee_khr"])),
            ),
        )

    async def get_position_by_user_and_ticker(
        self, telegram_chat_id: int, ticker: str
    ) -> Optional[Position]:
        res = await self._db.execute(
            text("""
                SELECT p.*, b.buy_fee_rate, b.sell_fee_rate, b.min_fee_khr
                FROM positions p
                JOIN broker_profiles b ON p.broker_id = b.id
                WHERE p.telegram_chat_id = :chat_id AND p.ticker = :ticker
            """),
            {"chat_id": telegram_chat_id, "ticker": ticker.upper()},
        )
        row = res.mappings().first()
        return self._map_position(row) if row else None

    async def get_position_by_id(self, position_id: int) -> Optional[Position]:
        res = await self._db.execute(
            text("""
                SELECT p.*, b.buy_fee_rate, b.sell_fee_rate, b.min_fee_khr
                FROM positions p
                JOIN broker_profiles b ON p.broker_id = b.id
                WHERE p.id = :pid
            """),
            {"pid": position_id},
        )
        row = res.mappings().first()
        return self._map_position(row) if row else None

    async def get_user_portfolio(
        self, telegram_chat_id: int
    ) -> list[tuple[Position, StockTick, list[ExitAlert]]]:
        res = await self._db.execute(
            text("""
                SELECT p.*, b.buy_fee_rate, b.sell_fee_rate, b.min_fee_khr,
                       s.last_price_khr, s.best_bid_khr, s.best_bid_volume, s.daily_fx_khr_usd
                FROM positions p
                JOIN broker_profiles b ON p.broker_id = b.id
                JOIN stocks s ON p.ticker = s.ticker
                WHERE p.telegram_chat_id = :chat_id AND p.total_shares > 0
                ORDER BY p.ticker ASC
            """),
            {"chat_id": telegram_chat_id},
        )
        rows = res.mappings().all()
        portfolio: list[tuple[Position, StockTick, list[ExitAlert]]] = []

        for r in rows:
            pos = self._map_position(r)
            tick = StockTick(
                ticker=r["ticker"],
                last_price_khr=r["last_price_khr"],
                best_bid_khr=r["best_bid_khr"] or r["last_price_khr"],
                best_bid_volume=r["best_bid_volume"] or 0,
                fx_khr_usd=r["daily_fx_khr_usd"],
            )
            alerts = await self._fetch_alerts_for_position(pos.id)
            portfolio.append((pos, tick, alerts))
        return portfolio

    async def _fetch_alerts_for_position(self, position_id: int) -> list[ExitAlert]:
        res = await self._db.execute(
            text("""
                SELECT id, position_id, trigger_type, target_value, target_exec_price_khr, is_active
                FROM exit_alerts
                WHERE position_id = :pid AND is_active = TRUE
            """),
            {"pid": position_id},
        )
        alerts: list[ExitAlert] = []
        for a in res.mappings().all():
            t_val = Decimal(str(a["target_value"]))
            alerts.append(
                ExitAlert(
                    id=a["id"],
                    position_id=a["position_id"],
                    trigger_type=a["trigger_type"],
                    target_value=t_val,
                    target_exec_price_khr=a["target_exec_price_khr"],
                    is_active=a["is_active"],
                    strategy=StrategyFactory.create(a["trigger_type"], t_val),
                )
            )
        return alerts

    async def get_active_positions_with_alerts(
        self, ticker: str
    ) -> list[tuple[Position, list[ExitAlert]]]:
        res = await self._db.execute(
            text("""
                SELECT p.*, b.buy_fee_rate, b.sell_fee_rate, b.min_fee_khr
                FROM positions p
                JOIN broker_profiles b ON p.broker_id = b.id
                WHERE p.ticker = :ticker AND p.total_shares > 0
            """),
            {"ticker": ticker.upper()},
        )
        results: list[tuple[Position, list[ExitAlert]]] = []
        for row in res.mappings().all():
            pos = self._map_position(row)
            alerts = await self._fetch_alerts_for_position(pos.id)
            if alerts:
                results.append((pos, alerts))
        return results

    async def save_position_and_transaction(
        self, position: Position, side: str, shares: int, price_khr: int, fee_khr: Decimal
    ) -> Position:
        await self._db.execute(
            text("""
                INSERT INTO stocks (ticker, company_name, last_price_khr, best_bid_khr)
                VALUES (:t, :t, :p, :p) ON CONFLICT (ticker) DO NOTHING
            """),
            {"t": position.ticker, "p": price_khr},
        )

        if position.id is None:
            ins = await self._db.execute(
                text("""
                    INSERT INTO positions (
                        user_id, telegram_chat_id, ticker, broker_id,
                        total_shares, total_cost_khr, avg_cost_per_share_khr, breakeven_price_khr
                    )
                    VALUES (:uid, :chat_id, :ticker, :bid, :sh, :cost, :avg, :be)
                    RETURNING id
                """),
                {
                    "uid": position.user_id,
                    "chat_id": position.telegram_chat_id,
                    "ticker": position.ticker,
                    "bid": position.broker_id,
                    "sh": position.shares,
                    "cost": position.total_cost_khr,
                    "avg": position.avg_cost_per_share_khr,
                    "be": position.executable_breakeven_khr,
                },
            )
            position.id = ins.scalar_one()
        else:
            await self._db.execute(
                text("""
                    UPDATE positions
                    SET total_shares = :sh,
                        total_cost_khr = :cost,
                        avg_cost_per_share_khr = :avg,
                        breakeven_price_khr = :be
                    WHERE id = :pid
                """),
                {
                    "sh": position.shares,
                    "cost": position.total_cost_khr,
                    "avg": position.avg_cost_per_share_khr,
                    "be": position.executable_breakeven_khr,
                    "pid": position.id,
                },
            )

        await self._db.execute(
            text("""
                INSERT INTO transactions (position_id, side, shares, price_khr, fee_khr)
                VALUES (:pid, :side, :sh, :price, :fee)
            """),
            {
                "pid": position.id,
                "side": side,
                "sh": shares,
                "price": price_khr,
                "fee": fee_khr,
            },
        )
        await self._db.commit()
        return position

    async def create_exit_alert(self, alert: ExitAlert) -> ExitAlert:
        ins = await self._db.execute(
            text("""
                INSERT INTO exit_alerts (position_id, trigger_type, target_value, target_exec_price_khr, is_active)
                VALUES (:pid, :ttype, :tval, :exec_p, TRUE)
                RETURNING id
            """),
            {
                "pid": alert.position_id,
                "ttype": alert.trigger_type,
                "tval": alert.target_value,
                "exec_p": alert.target_exec_price_khr,
            },
        )
        alert.id = ins.scalar_one()
        await self._db.commit()
        return alert

    async def mark_alert_triggered(self, alert_id: int) -> None:
        await self._db.execute(
            text("""
                UPDATE exit_alerts
                SET is_active = FALSE, last_triggered_at = NOW()
                WHERE id = :aid
            """),
            {"aid": alert_id},
        )
        await self._db.commit()