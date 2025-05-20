import logging
import sys

def setup_logging():
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Clear any existing handlers
    root_logger.addHandler(handler)

# Reuse central logger
logger = logging.getLogger("arb-bot")

def log_opportunity(
    base: str,
    quote: str,
    buy_exchange: str,
    sell_exchange: str,
    buy_price: float,
    sell_price: float,
    spread_pct: float,
    preview: bool = True,
):
    """
    Logs detected arbitrage opportunity in human-readable format.
    """
    pair = f"{base}/{quote}"
    message = (
        f"🟢 Opportunity: {pair} | "
        f"Buy on {buy_exchange} @ {buy_price:.4f}, "
        f"Sell on {sell_exchange} @ {sell_price:.4f} | "
        f"Spread: {spread_pct:.2f}% | "
        f"{'Preview' if preview else 'Live'}"
    )
    logger.info(message)
