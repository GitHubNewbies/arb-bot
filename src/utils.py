import logging
from decimal import Decimal
from src.trader import execute_order
from src.helpers.market import get_live_price, get_trade_quantity, get_best_opportunity

logger = logging.getLogger("arb-bot")

def scan_market(pairs: list, session):
    logger.info(f"Starting market scan for {len(pairs)} pairs")

    for pair in pairs:
        try:
            # Dynamically evaluate the best trading opportunity
            opportunity = get_best_opportunity(pair)
            if not opportunity:
                logger.info(f"No arbitrage opportunity for {pair}")
                continue

            exchange = opportunity["exchange"]
            side = opportunity["side"]
            price = Decimal(str(opportunity["price"]))

            # Calculate trade quantity using balance, precision, and strategy logic
            quantity = get_trade_quantity(exchange, pair, price, side)

            logger.info(f"Preparing to execute trade: {side} {quantity} {pair} @ {price} on {exchange}")
            execute_order(exchange, pair, side, quantity, price)

        except Exception as e:
            logger.exception(f"Error scanning pair {pair} on exchange {exchange}")
