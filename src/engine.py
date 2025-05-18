import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from src.helpers.market import get_live_price, get_trade_quantity
from src.exchanges.registry import get_exchange_adapter
from src.trader import execute_order

logger = logging.getLogger("arb-bot")

def scan_market(pairs: list[str], session: Session):
    logger.info(f"📊 Starting market scan for {len(pairs)} pairs")
    for pair in pairs:
        for exchange in ["binance", "bybit"]:
            try:
                adapter = get_exchange_adapter(exchange)
                price = get_live_price(pair, exchange)
                quantity = get_trade_quantity(pair, price, exchange, "BUY")

                if quantity <= 0:
                    logger.warning(f"⚠️ Computed quantity too low for {pair} | Balance: {quantity}, Price: {price}")
                    logger.warning(f"⚠️ Skipping {pair} on {exchange}: quantity is zero.")
                    continue

                logger.info(f"📈 {exchange.upper()} {pair} → Price: {price}, Qty: {quantity}")
                execute_order(exchange, pair, "BUY", quantity, price)
            except Exception as e:
                logger.error(f"❌ Failed to fetch price for {pair} on {exchange}: {e}")
                logger.warning(f"⚠️ Invalid price data for {pair} — skipping")
