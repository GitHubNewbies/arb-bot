from src.exchanges.binance import BinanceAdapter
from src.exchanges.bybit import BybitAdapter

def get_exchange_adapter(exchange: str):
    if exchange == "binance":
        return BinanceAdapter()
    elif exchange == "bybit":
        return BybitAdapter()
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")
