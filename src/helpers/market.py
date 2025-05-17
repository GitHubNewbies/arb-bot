import logging
from decimal import Decimal
from src.trader import fetch_balance, fetch_precision, fetch_price

logger = logging.getLogger("arb-bot")

def get_live_price(exchange: str, pair: str) -> Decimal:
    try:
        return Decimal(str(fetch_price(exchange, pair)))
    except Exception as e:
        logger.error(f"Failed to fetch price for {pair} on {exchange}: {e}")
        raise

def get_trade_quantity(exchange: str, pair: str, price: Decimal, side: str) -> Decimal:
    try:
        balance = fetch_balance(exchange, side)
        precision = fetch_precision(exchange, pair)

        raw_qty = balance / price
        factor = Decimal("1e-{0}".format(precision))
        quantity = (raw_qty // factor) * factor
        return quantity
    except Exception as e:
        logger.error(f"Failed to calculate trade quantity for {pair} on {exchange}: {e}")
        raise

def get_best_opportunity(pair: str) -> dict:
    # Placeholder logic for live environment: this should be replaced with real strategy evaluation
    # For now, assume all opportunities are on Binance and we BUY
    try:
        return {
            "exchange": "binance",
            "side": "BUY",
            "price": float(fetch_price("binance", pair))
        }
    except Exception as e:
        logger.warning(f"No opportunity available for {pair}: {e}")
        return {}
