# app/presentation/routers/portfolio_api.py
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from app.domain.interfaces import IPositionRepo
from app.application.record_transaction import RecordTransactionUseCase
from app.infrastructure.observers.websocket_observer import ws_manager
from app.presentation.dependencies import get_position_repo, get_record_transaction_use_case

router = APIRouter( tags=["Flutter Portfolio API"])


class TradeRequest(BaseModel):
    telegram_chat_id: int
    ticker: str = Field(..., examples=["ABC"])
    shares: int = Field(..., gt=0, examples=[1000])
    price_khr: int = Field(..., gt=0, examples=[10000])


class AlertCreateRequest(BaseModel):
    telegram_chat_id: int
    ticker: str = Field(..., examples=["ABC"])
    trigger_type: str = Field("TARGET_NET_ROI_PCT", examples=["TARGET_NET_ROI_PCT", "STOP_LOSS_KHR"])
    target_value: Decimal = Field(..., examples=[Decimal("12.0")])


@router.get("/api/portfolio/{telegram_chat_id}")
async def get_portfolio(
    telegram_chat_id: int,
    repo: IPositionRepo = Depends(get_position_repo),
):
    items = await repo.get_user_portfolio(telegram_chat_id)
    response = []
    for pos, tick, alerts in items:
        exec_price = tick.executable_exit_price_khr
        net_profit_khr = pos.net_profit_khr_at(exec_price)
        response.append(
            {
                "position_id": pos.id,
                "ticker": pos.ticker,
                "shares": pos.shares,
                "total_cost_khr": float(pos.total_cost_khr),
                "avg_cost_per_share_khr": float(round(pos.avg_cost_per_share_khr, 2)),
                "breakeven_khr": pos.executable_breakeven_khr,
                "last_price_khr": tick.last_price_khr,
                "best_bid_khr": tick.best_bid_khr,
                "net_profit_khr": int(net_profit_khr),
                "net_profit_usd": float(round(net_profit_khr / tick.fx_khr_usd, 2)),
                "net_roi_pct": float(round(pos.net_roi_pct_at(exec_price), 2)),
                "sell_fee_rate": float(pos.fee_policy.sell_fee_rate),
                "active_alerts": [
                    {
                        "alert_id": a.id,
                        "trigger_type": a.trigger_type,
                        "target_value": float(a.target_value),
                        "target_exec_price_khr": a.target_exec_price_khr,
                    }
                    for a in alerts
                ],
            }
        )
    return {"positions": response}


@router.post("/api/portfolio/buy")
async def record_buy_endpoint(
    payload: TradeRequest,
    use_case: RecordTransactionUseCase = Depends(get_record_transaction_use_case),
):
    pos, fee = await use_case.record_buy(
        telegram_chat_id=payload.telegram_chat_id,
        ticker=payload.ticker,
        shares=payload.shares,
        price_khr=payload.price_khr,
    )
    return {
        "position_id": pos.id,
        "ticker": pos.ticker,
        "total_shares": pos.shares,
        "fee_charged_khr": float(fee),
        "breakeven_price_khr": pos.executable_breakeven_khr,
    }


@router.post("/api/portfolio/sell")
async def record_sell_endpoint(
    payload: TradeRequest,
    use_case: RecordTransactionUseCase = Depends(get_record_transaction_use_case),
):
    try:
        pos, fee, realized_profit = await use_case.record_sell(
            telegram_chat_id=payload.telegram_chat_id,
            ticker=payload.ticker,
            shares=payload.shares,
            price_khr=payload.price_khr,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "position_id": pos.id,
        "ticker": pos.ticker,
        "remaining_shares": pos.shares,
        "sell_fee_khr": float(fee),
        "realized_net_profit_khr": float(realized_profit),
    }


@router.post("/api/portfolio/alerts")
async def create_alert_endpoint(
    payload: AlertCreateRequest,
    use_case: RecordTransactionUseCase = Depends(get_record_transaction_use_case),
):
    try:
        pos, alert = await use_case.set_exit_alert(
            telegram_chat_id=payload.telegram_chat_id,
            ticker=payload.ticker,
            trigger_type=payload.trigger_type,
            target_value=payload.target_value,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "alert_id": alert.id,
        "ticker": pos.ticker,
        "trigger_type": alert.trigger_type,
        "target_exec_price_khr": alert.target_exec_price_khr,
        "breakeven_price_khr": pos.executable_breakeven_khr,
    }


@router.websocket("/ws/prices")
async def websocket_prices_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)