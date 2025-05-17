from src.helpers.market import get_live_price, get_trade_quantity, get_best_opportunity

def fetch_market_analysis(pair: str, side: str = "BUY"):
    opportunity = get_best_opportunity(pair)
    if not opportunity:
        return None

    exchange = opportunity["exchange"]
    price = get_live_price(exchange, pair)
    quantity = get_trade_quantity(exchange, pair, price, side)

    return {
        "exchange": exchange,
        "side": side,
        "price": price,
        "quantity": quantity
    }
