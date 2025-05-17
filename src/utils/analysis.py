import logging
from decimal import Decimal
from src.helpers.market import get_live_price, get_trade_quantity

logger = logging.getLogger("arb-bot")

def fetch_market_analysis(pair: str, exchange: str = "binance", side: str = "BUY") -> dict | None:
    try:
        price = get_live_price(exchange, pair)
        if price <= 0:
            logger.warning(f"⚠️ Skipping {pair} on {exchange}: price is zero.")
            return None

        quantity = get_trade_quantity(exchange, pair, price, side)
        if quantity <= 0:
            logger.warning(f"⚠️ Skipping {pair} on {exchange}: quantity is zero.")
            return None

        return {
            "pair": pair,
            "exchange": exchange,
            "side": side,
            "price": price,
            "quantity": quantity,
        }

    except Exception as e:
        logger.exception(f"❌ Market analysis failed for {pair} on {exchange}: {e}")
        return None
