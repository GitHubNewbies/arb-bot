import logging
from decimal import Decimal
from src.utils import fetch_market_analysis
from src.trader import execute_order

logger = logging.getLogger("arb-bot")

def scan_market(pairs: list, session):
    logger.info(f"Starting market scan for {len(pairs)} pairs")

    for pair in pairs:
        try:
            opportunity = fetch_market_analysis(pair)
            if not opportunity:
                logger.info(f"No arbitrage opportunity for {pair}")
                continue

            exchange = opportunity["exchange"]
            side = opportunity["side"]
            price = Decimal(str(opportunity["price"]))
            quantity = opportunity["quantity"]

            logger.info(f"Preparing to execute trade: {side} {quantity} {pair} @ {price} on {exchange}")
            execute_order(exchange, pair, side, quantity, price)

        except Exception as e:
            logger.exception(f"Error scanning pair {pair}")
