import logging
from src.exchanges.binance import BinanceAdapter
from src.exchanges.bybit import BybitAdapter

logger = logging.getLogger("arb-bot")

def get_common_pairs() -> list[str]:
    """
    Fetches tradable pairs from Binance and Bybit,
    returns the common USDC-quoted pairs in the format BASE/USDC.
    """
    try:
        binance_pairs = set(BinanceAdapter().fetch_tradable_pairs())
        bybit_pairs = set(BybitAdapter().fetch_tradable_pairs())

        # Ensure uppercase and consistent format
        binance_usdc = {p.upper() for p in binance_pairs if p.upper().endswith("/USDC")}
        bybit_usdc = {p.upper() for p in bybit_pairs if p.upper().endswith("/USDC")}

        common = sorted(list(binance_usdc & bybit_usdc))
        logger.info(f"📦 Common tradable USDC pairs: {common}")
        return common

    except Exception as e:
        logger.exception("❌ Failed to fetch common pairs")
        return []
