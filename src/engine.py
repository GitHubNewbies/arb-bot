import logging
from decimal import Decimal
from src.helpers.market import get_live_price, get_trade_quantity
from src.trader import execute_order
from src.utils.pairs import get_pairs_to_monitor

logger = logging.getLogger("arb-bot")

def scan_market():
    pairs = get_pairs_to_monitor()
    logger.info(f"📊 Starting market scan for {len(pairs)} pairs")

    for pair in pairs:
        try:
            # Prices
            binance_price = get_live_price("binance", pair)
            bybit_price = get_live_price("bybit", pair)

            if binance_price <= 0 or bybit_price <= 0:
                logger.warning(f"⚠️ Invalid price data for {pair} — skipping")
                continue

            # Compare for opportunity
            opportunities = []
            if bybit_price > binance_price:
                spread = ((bybit_price - binance_price) / binance_price) * 100
                opportunities.append({
                    "buy_exchange": "binance",
                    "sell_exchange": "bybit",
                    "buy_price": binance_price,
                    "sell_price": bybit_price,
                    "spread_pct": round(spread, 4),
                    "side": "BUY"
                })
            elif binance_price > bybit_price:
                spread = ((binance_price - bybit_price) / bybit_price) * 100
                opportunities.append({
                    "buy_exchange": "bybit",
                    "sell_exchange": "binance",
                    "buy_price": bybit_price,
                    "sell_price": binance_price,
                    "spread_pct": round(spread, 4),
                    "side": "BUY"
                })

            if not opportunities:
                logger.info(f"No arbitrage opportunity for {pair}")
                continue

            best = sorted(opportunities, key=lambda x: x["spread_pct"], reverse=True)[0]
            logger.info(
                f"📈 Spread for {pair}: {best['spread_pct']}% "
                f"[BUY on {best['buy_exchange']} @ {best['buy_price']}, "
                f"SELL on {best['sell_exchange']} @ {best['sell_price']}]"
            )

            # Quantity validation
            buy_qty = get_trade_quantity(best["buy_exchange"], pair, Decimal(best["buy_price"]), "BUY")
            sell_qty = get_trade_quantity(best["sell_exchange"], pair, Decimal(best["sell_price"]), "SELL")

            trade_qty = min(buy_qty, sell_qty)

            if trade_qty <= 0:
                logger.warning(f"⚠️ Skipping {pair}: quantity is zero.")
                continue

            # Execute both legs of the arbitrage
            logger.info(f"🛒 Preparing to execute arbitrage for {pair} — Quantity: {trade_qty}")
            execute_order(best["buy_exchange"], pair, "BUY", trade_qty, Decimal(best["buy_price"]))
            execute_order(best["sell_exchange"], pair, "SELL", trade_qty, Decimal(best["sell_price"]))

        except Exception as e:
            logger.error(f"❌ Error scanning pair {pair}", exc_info=True)
