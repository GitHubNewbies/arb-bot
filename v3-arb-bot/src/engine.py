import time, asyncio
import ccxt.async_support as ccxt
from .config import *
from .db import log_event

binance = ccxt.binance({
    "apiKey": BINANCE_API_KEY, "secret": BINANCE_SECRET,
    "enableRateLimit": True,
})
bybit   = ccxt.bybit({
    "apiKey": BYBIT_API_KEY, "secret": BYBIT_SECRET,
    "enableRateLimit": True,
})

_last_trade = 0.0

async def confirm_fill(ex, oid, pair):
    for _ in range(6):
        if (await ex.fetch_order(oid, pair))["status"] == "closed":
            return True
        await asyncio.sleep(0.5)
    return False

async def get_valid_amount(exchange, pair, target_usd):
    market = exchange.markets[pair]
    ticker = await exchange.fetch_ticker(pair)
    price  = ticker["bid"]
    min_cost   = market["limits"]["cost"]["min"]
    min_amount = market["limits"]["amount"]["min"]
    raw_amt    = target_usd / price
    amt = max(raw_amt, min_amount, min_cost / price)
    precision = market["precision"]["amount"]
    return round(amt, precision)

async def arbitrage():
    global _last_trade
    now = time.time()
    if now - _last_trade < COOLDOWN_SECONDS:
        return

    for pair in PAIRS:
        ob_b = await binance.fetch_order_book(pair)
        ob_y = await bybit.fetch_order_book(pair)
        bid_b, ask_b = ob_b["bids"][0][0], ob_b["asks"][0][0]
        bid_y, ask_y = ob_y["bids"][0][0], ob_y["asks"][0][0]

        spread1 = (ask_y - bid_b) / bid_b
        log_event(pair, "scan", bid_b, ask_y, spread1, 0.0)

        if DESIRED_NOTIONAL_USD > 0:
            size_b = await get_valid_amount(binance, pair, DESIRED_NOTIONAL_USD)
            size_y = await get_valid_amount(bybit,   pair, DESIRED_NOTIONAL_USD)
        else:
            size_b = size_y = TRADE_SIZE

        if spread1 >= SPREAD_THRESHOLD:
            buy = await binance.create_market_buy_order(pair, size_b)
            if await confirm_fill(binance, buy["id"], pair):
                sell = await bybit.create_market_sell_order(pair, size_b)
                if await confirm_fill(bybit, sell["id"], pair):
                    profit = (ask_y - bid_b) * size_b
                    log_event(pair, "B→Y", bid_b, ask_y, spread1, profit)
            _last_trade = now

        spread2 = (bid_y - ask_b) / ask_b
        if spread2 >= SPREAD_THRESHOLD:
            buy = await bybit.create_market_buy_order(pair, size_y)
            if await confirm_fill(bybit, buy["id"], pair):
                sell = await binance.create_market_sell_order(pair, size_y)
                if await confirm_fill(binance, sell["id"], pair):
                    profit = (bid_y - ask_b) * size_y
                    log_event(pair, "Y→B", ask_b, bid_y, spread2, profit)
            _last_trade = now
