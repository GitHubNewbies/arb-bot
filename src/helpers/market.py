# src/helpers/market.py

import logging
from decimal import Decimal
from src.exchanges.registry import get_exchange_adapter

logger = logging.getLogger("arb-bot")

def get_live_price(exchange: str, pair: str) -> Decimal:
    try:
        adapter = get_exchange_adapter(exchange)
        return adapter.fetch_price(pair)
    except Exception as e:
        logger.error(f"❌ Failed to fetch price for {pair} on {exchange}: {e}", exc_info=True)
        return Decimal("0")

def get_trade_quantity(exchange: str, pair: str, price: Decimal, side: str) -> Decimal:
    try:
        adapter = get_exchange_adapter(exchange)
        return adapter.calculate_quantity(pair, price, side)
    except Exception as e:
        logger.error(f"❌ Trade quantity error for {pair} on {exchange} ({side}): {e}", exc_info=True)
        return Decimal("0")

def get_best_opportunity(pair: str) -> dict | None:
    try:
        binance_price = get_live_price("binance", pair)
        bybit_price = get_live_price("bybit", pair)

        if binance_price <= 0 or bybit_price <= 0:
            logger.warning(f"⚠️ Skipping {pair} due to missing price data")
            return None

        opportunities = []

        if bybit_price > binance_price:
            spread = ((bybit_price - binance_price) / binance_price) * 100
            opportunities.append({
                "buy_exchange": "binance",
                "sell_exchange": "bybit",
                "buy_price": binance_price,
                "sell_price": bybit_price,
                "spread_pct": round(spread, 4),
                "side": "BUY",
                "exchange": "binance",
            })

        if binance_price > bybit_price:
            spread = ((binance_price - bybit_price) / bybit_price) * 100
            opportunities.append({
                "buy_exchange": "bybit",
                "sell_exchange": "binance",
                "buy_price": bybit_price,
                "sell_price": binance_price,
                "spread_pct": round(spread, 4),
                "side": "BUY",
                "exchange": "bybit",
            })

        if not opportunities:
            return None

        best = sorted(opportunities, key=lambda x: x["spread_pct"], reverse=True)[0]
        logger.info(
            f"📈 Spread for {pair}: {best['spread_pct']}% "
            f"[BUY on {best['buy_exchange']} @ {best['buy_price']}, "
            f"SELL on {best['sell_exchange']} @ {best['sell_price']}]"
        )
        return best

    except Exception as e:
        logger.exception(f"❌ Failed to evaluate spread for {pair}")
        return None
