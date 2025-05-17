import logging
from decimal import Decimal

from src.exchanges.binance import fetch_binance_price, calculate_binance_quantity
from src.exchanges.bybit import fetch_bybit_price, calculate_bybit_quantity

logger = logging.getLogger("arb-bot")


def get_live_price(exchange: str, pair: str) -> Decimal:
    if exchange == "binance":
        return fetch_binance_price(pair)
    elif exchange == "bybit":
        return fetch_bybit_price(pair)
    else:
        raise ValueError(f"❌ Unsupported exchange: {exchange}")


def get_trade_quantity(exchange: str, pair: str, price: Decimal, side: str) -> Decimal:
    if exchange == "binance":
        return calculate_binance_quantity(pair, price, side)
    elif exchange == "bybit":
        return calculate_bybit_quantity(pair, price, side)
    else:
        raise ValueError(f"❌ Unsupported exchange: {exchange}")


def get_best_opportunity(pair: str) -> dict | None:
    try:
        binance_price = fetch_binance_price(pair)
        bybit_price = fetch_bybit_price(pair)

        if not binance_price or not bybit_price:
            logger.warning(f"Missing prices for {pair}")
            return None

        opportunities = []

        # Option 1: Buy on Binance, Sell on Bybit
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

        # Option 2: Buy on Bybit, Sell on Binance
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
        logger.exception(f"Failed to evaluate spread for {pair}")
        return None
