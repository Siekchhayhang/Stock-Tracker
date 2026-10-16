# app/infrastructure/observers/telegram_observer.py
import os
import httpx
from app.domain.entities import StockTick, Position, ExitAlert


class TelegramAlertObserver:
    """SRP: Formats and dispatches exit notifications to Telegram users."""

    def __init__(self, bot_token: str | None = None):
        token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self._send_url = f"https://api.telegram.org/bot{token}/sendMessage"

    async def on_prices_updated(self, ticks: dict[str, StockTick]) -> None:
        # Telegram only fires when an exit alert is triggered, not on every 15s tick
        pass

    async def on_alert_triggered(
        self, position: Position, tick: StockTick, alert: ExitAlert
    ) -> None:
        exec_price = tick.executable_exit_price_khr
        net_profit_khr = position.net_profit_khr_at(exec_price)
        net_profit_usd = net_profit_khr / tick.fx_khr_usd
        net_roi_pct = position.net_roi_pct_at(exec_price)

        badge = (
            "🟢 TAKE-PROFIT TRIGGERED"
            if "TARGET" in alert.trigger_type
            else "🔴 STOP-LOSS TRIGGERED"
        )
        sign = "+" if net_profit_khr >= 0 else ""

        message = (
            f"<b>{badge}: #{position.ticker} (CSX)</b>\n\n"
            f"• <b>Executable Bid/Price:</b> {exec_price:,} KHR\n"
            f"• <b>Trigger Target:</b> {alert.target_exec_price_khr:,} KHR\n"
            f"• <b>Your Tick Break-Even:</b> {position.executable_breakeven_khr:,} KHR\n"
            f"• <b>Position Size:</b> {position.shares:,} shares\n"
            f"• <b>Est. Net P&L (After Fees):</b> {sign}{int(net_profit_khr):,} KHR ({sign}${net_profit_usd:,.2f})\n"
            f"• <b>Net Return:</b> {sign}{net_roi_pct:.2f}%"
        )

        payload = {
            "chat_id": position.telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "✅ Log Full Exit",
                            "callback_data": f"sell_all:{position.id}:{exec_price}",
                        },
                        {
                            "text": "⏰ Snooze +2% Higher",
                            "callback_data": f"bump_target:{position.id}:0.02",
                        },
                    ]
                ]
            },
        }

        async with httpx.AsyncClient(timeout=8.0) as client:
            await client.post(self._send_url, json=payload)