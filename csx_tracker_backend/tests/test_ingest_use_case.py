# tests/test_ingest_use_case.py
import pytest
from decimal import Decimal
from app.domain.policies import Position, MarketQuote
from app.domain.strategies import TargetNetRoiStrategy

def test_csx_tick_alignment_and_target_trigger():
    # 1,000 ABC bought @ 10,000 KHR + 0.5% buy fee = 10,050,000 KHR total cost
    pos = Position(
        id=1, user_chat_id=999, ticker="ABC", shares=1000,
        total_cost_khr=Decimal("10050000"),
        buy_fee_rate=Decimal("0.005"), sell_fee_rate=Decimal("0.005")
    )
    # Break-even raw is 10,100.50 -> must align to 10,120 KHR (20 KHR tick)
    assert pos.executable_breakeven_khr == 10120

    # +10% Net ROI strategy -> requires 11,120 KHR executable bid
    strategy = TargetNetRoiStrategy(target_roi_pct=Decimal("10.0"), require_bid_support=True)
    assert strategy.target_executable_price_khr(pos) == 11120

    # Quote with high last_price (11,200) but thin best_bid (11,080) should NOT false-trigger
    thin_quote = MarketQuote(ticker="ABC", last_price_khr=11200, best_bid_khr=11080, best_bid_volume=500)
    assert strategy.is_satisfied(pos, thin_quote) is False

    # Quote where best_bid reaches 11,120 KHR triggers cleanly
    liquid_quote = MarketQuote(ticker="ABC", last_price_khr=11120, best_bid_khr=11120, best_bid_volume=2000)
    assert strategy.is_satisfied(pos, liquid_quote) is True