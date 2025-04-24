import pytest, asyncio
import ccxt
from src.engine import get_valid_amount

@pytest.mark.asyncio
async def test_notional_sizing():
    ex = ccxt.binance({"apiKey":"","secret":"","enableRateLimit":True})
    ex.markets = {"FAKE/USDC":{"limits":{"cost":{"min":10},"amount":{"min":0.001}},"precision":{"amount":3}}}
    ex.fetch_ticker = lambda p: {"bid":50}
    amt = await get_valid_amount(ex,"FAKE/USDC",50)
    assert amt == pytest.approx(1.0, rel=1e-3)
