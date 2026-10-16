# app/presentation/routers/telegram_webhook.py
import os
from decimal import Decimal
import httpx
from fastapi import APIRouter, Request, Depends

from app.domain.interfaces import IPositionRepo
from app.application.record_transaction import RecordTransactionUseCase
from app.presentation.dependencies import get_position_repo, get_record_transaction_use_case

router = APIRouter(prefix="/api/telegram", tags=["Telegram Bot Webhook"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_telegram_reply(chat_id: int, html_text: str) -> None:
    async with httpx.AsyncClient(timeout=8.0) as client:
        await client.post(
            f"{TELEGRAM_API_BASE}/sendMessage",
            json={"chat_id": chat_id, "text": html_text, "parse_mode": "HTML"},
        )


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    use_case: RecordTransactionUseCase = Depends(get_record_transaction_use_case),
    repo: IPositionRepo = Depends(get_position_repo),
):
    update = await request.json()

    # 1. Handle Inline Keyboard Button Callbacks
    if "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        data = cb.get("data", "")

        try:
            if data.startswith("sell_all:"):
                _, pos_id_str, price_str = data.split(":")
                pos, realized = await use_case.record_full_exit_by_position_id(
                    int(pos_id_str), int(price_str)
                )
                sign = "+" if realized >= 0 else ""
                await send_telegram_reply(
                    chat_id,
                    f"💰 <b>Closed Full Position: #{pos.ticker}</b>\n"
                    f"• <b>Realized Net P&L:</b> <code>{sign}{int(realized):,} KHR</code>",
                )
            elif data.startswith("bump_target:"):
                _, pos_id_str, bump_str = data.split(":")
                pos, alert = await use_case.bump_alert_target(
                    int(pos_id_str), Decimal(bump_str)
                )
                await send_telegram_reply(
                    chat_id,
                    f"⏰ <b>Snoozed #{pos.ticker} Alert</b>\n"
                    f"New CSX tick-aligned trigger armed at <code>{alert.target_exec_price_khr:,} KHR</code>.",
                )
        except ValueError as exc:
            await send_telegram_reply(chat_id, f"⚠️ {exc}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{TELEGRAM_API_BASE}/answerCallbackQuery",
                json={"callback_query_id": cb["id"]},
            )
        return {"ok": True}

    # 2. Handle Slash Commands (/buy, /sell, /target, /status)
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text_body = (msg.get("text") or "").strip()

    if not chat_id or not text_body.startswith("/"):
        return {"ok": True}

    parts = text_body.split()
    cmd = parts[0].lower()

    try:
        if cmd == "/buy" and len(parts) == 4:
            ticker = parts[1].upper()
            shares = int(parts[2].replace(",", ""))
            price_khr = int(parts[3].replace(",", ""))
            pos, fee = await use_case.record_buy(chat_id, ticker, shares, price_khr)
            await send_telegram_reply(
                chat_id,
                f"✅ <b>Logged Buy: #{pos.ticker}</b>\n"
                f"• <b>Tranche:</b> {shares:,} sh @ {price_khr:,} KHR (Fee: {int(fee):,} KHR)\n"
                f"• <b>Total Shares:</b> {pos.shares:,}\n"
                f"• <b>All-In Avg Cost:</b> {pos.avg_cost_per_share_khr:,.2f} KHR\n"
                f"• <b>CSX Tick Break-Even:</b> <code>{pos.executable_breakeven_khr:,} KHR</code>",
            )

        elif cmd == "/sell" and len(parts) == 4:
            ticker = parts[1].upper()
            shares = int(parts[2].replace(",", ""))
            price_khr = int(parts[3].replace(",", ""))
            pos, fee, realized = await use_case.record_sell(chat_id, ticker, shares, price_khr)
            sign = "+" if realized >= 0 else ""
            await send_telegram_reply(
                chat_id,
                f"💸 <b>Logged Sale: #{pos.ticker}</b>\n"
                f"• <b>Sold:</b> {shares:,} sh @ {price_khr:,} KHR (Fee: {int(fee):,} KHR)\n"
                f"• <b>Realized Net P&L:</b> <code>{sign}{int(realized):,} KHR</code>\n"
                f"• <b>Remaining Shares:</b> {pos.shares:,}",
            )

        elif cmd == "/target" and len(parts) == 3:
            ticker = parts[1].upper()
            roi_pct = Decimal(parts[2].replace("%", ""))
            pos, alert = await use_case.set_exit_alert(
                chat_id, ticker, "TARGET_NET_ROI_PCT", roi_pct
            )
            await send_telegram_reply(
                chat_id,
                f"🎯 <b>Exit Alert Armed: #{pos.ticker}</b>\n"
                f"• <b>Target Net ROI:</b> +{roi_pct:.1f}% (after fees)\n"
                f"• <b>CSX Trigger Price:</b> <code>{alert.target_exec_price_khr:,} KHR</code>\n"
                f"• <b>Break-Even Floor:</b> <code>{pos.executable_breakeven_khr:,} KHR</code>",
            )

        elif cmd == "/status":
            items = await repo.get_user_portfolio(chat_id)
            if not items:
                await send_telegram_reply(chat_id, "📭 Your CSX portfolio is currently empty.")
                return {"ok": True}

            lines = ["<b>📊 Live CSX Portfolio Status</b>\n"]
            for pos, tick, alerts in items:
                exec_p = tick.executable_exit_price_khr
                net_khr = pos.net_profit_khr_at(exec_p)
                roi = pos.net_roi_pct_at(exec_p)
                sign = "+" if net_khr >= 0 else ""
                target_str = (
                    f"{alerts[0].target_exec_price_khr:,} KHR" if alerts else "None"
                )
                lines.append(
                    f"<b>#{pos.ticker}</b> ({pos.shares:,} sh)\n"
                    f"  Live Bid: {exec_p:,} KHR | BE: {pos.executable_breakeven_khr:,} KHR\n"
                    f"  Net P&L: <b>{sign}{int(net_khr):,} KHR ({sign}{roi:.2f}%)</b> | Target: {target_str}\n"
                )
            await send_telegram_reply(chat_id, "\n".join(lines))

        else:
            await send_telegram_reply(
                chat_id,
                "<b>CSX Profit Tracker Commands:</b>\n"
                "• <code>/buy ABC 1000 10000</code>\n"
                "• <code>/sell ABC 500 10400</code>\n"
                "• <code>/target ABC 12</code> (+12% Net ROI)\n"
                "• <code>/status</code>",
            )
    except Exception as exc:
        await send_telegram_reply(chat_id, f"⚠️ Error: {exc}")

    return {"ok": True}