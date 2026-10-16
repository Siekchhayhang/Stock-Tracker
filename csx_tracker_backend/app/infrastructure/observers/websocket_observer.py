# app/infrastructure/observers/websocket_observer.py
from fastapi import WebSocket
from app.domain.entities import StockTick, Position, ExitAlert


class WebSocketConnectionManager:
    """Manages active Flutter WebSocket connections."""

    def __init__(self):
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

    async def broadcast_json(self, payload: dict) -> None:
        stale: list[WebSocket] = []
        for connection in self._active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                stale.append(connection)
        for dead in stale:
            self.disconnect(dead)


ws_manager = WebSocketConnectionManager()


class WebSocketAlertObserver:
    """SRP: Broadcasts live CSX price ticks and exit signals to Flutter WebSocket clients."""

    def __init__(self, manager: WebSocketConnectionManager = ws_manager):
        self._manager = manager

    async def on_prices_updated(self, ticks: dict[str, StockTick]) -> None:
        await self._manager.broadcast_json(
            {
                "event": "PRICE_UPDATE",
                "data": {
                    ticker: {
                        "last_price_khr": t.last_price_khr,
                        "best_bid_khr": t.best_bid_khr,
                        "volume": t.volume,
                    }
                    for ticker, t in ticks.items()
                },
            }
        )

    async def on_alert_triggered(
        self, position: Position, tick: StockTick, alert: ExitAlert
    ) -> None:
        exec_price = tick.executable_exit_price_khr
        await self._manager.broadcast_json(
            {
                "event": "EXIT_ALERT_TRIGGERED",
                "data": {
                    "position_id": position.id,
                    "ticker": position.ticker,
                    "trigger_type": alert.trigger_type,
                    "executable_price_khr": exec_price,
                    "net_profit_khr": int(position.net_profit_khr_at(exec_price)),
                    "net_roi_pct": float(round(position.net_roi_pct_at(exec_price), 2)),
                },
            }
        )