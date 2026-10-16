# app/infrastructure/market_providers/csx_html_scraper.py
import httpx
from bs4 import BeautifulSoup
from app.domain.entities import StockTick


class CSXHtmlScraper:
    """Fallback HTML scraper for csx.com.kh trade summary page."""

    CSX_URL = "https://csx.com.kh/en/market-data/stock/trade-summary"

    @staticmethod
    def _parse_int(text: str) -> int:
        cleaned = text.replace(",", "").strip()
        return int(cleaned) if cleaned.isdigit() else 0

    async def fetch_latest_ticks(self) -> dict[str, StockTick]:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; CSXProfitTracker/2.0)"}
        async with httpx.AsyncClient(timeout=15.0, headers=headers, verify=False) as client:
            resp = await client.get(self.CSX_URL)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        ticks: dict[str, StockTick] = {}

        for row in soup.select("table tr"):
            cols = [c.get_text(strip=True) for c in row.find_all("td")]
            if len(cols) >= 2 and cols[0].isalpha() and 2 <= len(cols[0]) <= 5:
                ticker = cols[0].upper()
                last_price = self._parse_int(cols[1])
                best_bid = self._parse_int(cols[8]) if len(cols) > 8 else last_price
                best_ask = self._parse_int(cols[9]) if len(cols) > 9 else 0
                volume = self._parse_int(cols[6]) if len(cols) > 6 else 0

                if last_price > 0:
                    ticks[ticker] = StockTick(
                        ticker=ticker,
                        last_price_khr=last_price,
                        best_bid_khr=best_bid or last_price,
                        best_ask_khr=best_ask,
                        volume=volume,
                    )
        return ticks