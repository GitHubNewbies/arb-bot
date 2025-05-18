import logging
from decimal import Decimal
from src.exchanges.registry import get_exchange_adapter

logger = logging.getLogger("arb-bot")

def get_live_price(exchange: str, pair: str) -> Decimal:
    adapter = get_exchange_adapter(exchange)
    try:
        return adapter.fetch_price(pair)
    except Exception as e:
        logger.error(f"❌ Failed to fetch price for {exchange} on {pair}: {e}")
        raise

def get_trade_quantity(exchange: str, pair: str, price: Decimal, side: str) -> Decimal:
    adapter = get_exchange_adapter(exchange)
    try:
        return adapter.calculate_quantity(pair, price, side)
    except Exception as e:
        logger.error(f"❌ Trade quantity error for {price} on {pair} ({side}): {e}")
        return Decimal("0.0")
