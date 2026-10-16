# app/infrastructure/market_providers/mef_dataef_client.py
from decimal import Decimal
import httpx
from app.domain.entities import StockTick


class MEFDataEFClient:
    """Primary real-time CSX data provider using official MEF DataEF JSON API."""

    SUMMARY_URL = "https://data.mef.gov.kh/api/v1/realtime-api/csx-summary"
    FX_URL = "https://data.mef.gov.kh/api/v1/realtime-api/exchange-rate"

    @staticmethod
    def _clean_int(val: object) -> int:
        if val is None:
            return 0
        cleaned = str(val).replace(",", "").split(".")[0].strip()
        return int(cleaned) if cleaned.isdigit() else 0

    async def fetch_latest_ticks(self) -> dict[str, StockTick]:
        headers = {"User-Agent": "CSXProfitTracker/2.0"}
        async with httpx.AsyncClient(timeout=12.0, headers=headers, verify=False) as client:
            resp = await client.get(self.SUMMARY_URL)
            resp.raise_for_status()
            payload = resp.json()

            fx_rate = Decimal("4065.00")
            try:
                fx_resp = await client.get(self.FX_URL)
                if fx_resp.status_code == 200:
                    fx_data = fx_resp.json().get("data", {})
                    if isinstance(fx_data, dict) and fx_data.get("khr_usd"):
                        fx_rate = Decimal(str(fx_data["khr_usd"]))
            except Exception:
                pass

        items = payload.get("data", payload) if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            return {}

        ticks: dict[str, StockTick] = {}
        for item in items:
            ticker = (
                item.get("stock_code") or item.get("ticker") or item.get("symbol") or ""
            ).strip().upper()
            if not ticker:
                continue

            last_price = self._clean_int(item.get("close_price") or item.get("last_price"))
            best_bid = self._clean_int(item.get("bid_price") or item.get("best_bid")) or last_price
            best_ask = self._clean_int(item.get("ask_price") or item.get("best_ask"))
            volume = self._clean_int(item.get("volume"))

            if last_price > 0:
                ticks[ticker] = StockTick(
                    ticker=ticker,
                    last_price_khr=last_price,
                    best_bid_khr=best_bid,
                    best_ask_khr=best_ask,
                    volume=volume,
                    fx_khr_usd=fx_rate,
                )
        return ticks