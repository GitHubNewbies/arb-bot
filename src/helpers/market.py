from src.exchanges.binance import fetch_binance_price, calculate_binance_quantity
from src.exchanges.bybit import fetch_bybit_price, calculate_bybit_quantity

def get_live_price(exchange, pair):
    if exchange == "binance":
        return fetch_binance_price(pair)
    elif exchange == "bybit":
        return fetch_bybit_price(pair)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")

def get_trade_quantity(exchange, pair, price, side):
    if exchange == "binance":
        return calculate_binance_quantity(pair, price, side)
    elif exchange == "bybit":
        return calculate_bybit_quantity(pair, price, side)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")

def get_best_opportunity(pair):
    # Temporarily hardcoded to test both exchanges; improve with real logic later.
    from random import choice
    exchange = choice(["binance", "bybit"])
    price = get_live_price(exchange, pair)
    return {
        "exchange": exchange,
        "side": "BUY",
        "price": price
    }
