import logging
from decimal import Decimal
from src.helpers.market import get_live_price, get_trade_quantity
from src.trader import execute_order
from src.database import get_db_session
from src.models import TradeLog

logger = logging.getLogger("arb-bot")

EXCHANGES = ["binance", "bybit"]

def scan_market(pairs: list[str], session):
    for pair in pairs:
        logger.info(f"🔍 Scanning {pair}")
        try:
            prices = {}
            quantities = {}

            for exchange in EXCHANGES:
                try:
                    price = get_live_price(exchange, pair)
                    quantity = get_trade_quantity(exchange, pair, price, "BUY")
                    if quantity > 0:
                        prices[exchange] = price
                        quantities[exchange] = quantity
                    else:
                        logger.warning(f"⚠️ Skipping {pair} on {exchange}: quantity is zero.")
                except Exception:
                    continue

            if len(prices) == 2:
                binance_price = prices["binance"]
                bybit_price = prices["bybit"]

                if bybit_price > binance_price * Decimal("1.005"):
                    logger.info(f"💰 Arbitrage opp: BUY on binance at {binance_price}, SELL on bybit at {bybit_price}")
                    execute_order("binance", pair, "BUY", quantities["binance"], binance_price)
                    execute_order("bybit", pair, "SELL", quantities["bybit"], bybit_price)

                    for exchange in EXCHANGES:
                        log = TradeLog(
                            exchange=exchange,
                            symbol=pair,
                            side="BUY" if exchange == "binance" else "SELL",
                            quantity=quantities[exchange],
                            price=prices[exchange],
                            status="executed",
                        )
                        session.add(log)

                    session.commit()
                else:
                    logger.info(f"ℹ️ No arbitrage opportunity for {pair}")

        except Exception as e:
            logger.error(f"❌ Error scanning pair {pair}: {e}")
