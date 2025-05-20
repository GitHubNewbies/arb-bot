from src.exchanges.binance import BinanceAdapter
from src.exchanges.bybit import BybitAdapter
from src.logger import get_logger

logger = get_logger(__name__, level="DEBUG")
import time
from typing import List

_cache_common_pairs = None
_cache_timestamp = 0
_CACHE_TTL_SECONDS = 600  # 10 minutes cache

def get_common_pairs() -> List[str]:
    """
    Fetches tradable pairs from Binance and Bybit,
    returns the common USDC-quoted pairs in the format BASE/USDC.

    Optional Suggestions:
    - Results are cached for 10 minutes to reduce redundant API calls.
    - Exceptions are explicitly caught as 'Exception as e'.
    """
    global _cache_common_pairs, _cache_timestamp

    now = time.time()
    if _cache_common_pairs is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _cache_common_pairs

    try:
        binance_adapter = BinanceAdapter()
        bybit_adapter = BybitAdapter()

        binance_pairs = set(binance_adapter.get_tradable_pairs())
        bybit_pairs = set(bybit_adapter.get_tradable_pairs())
        common_pairs = [pair for pair in binance_pairs.intersection(bybit_pairs) if pair.endswith("/USDC")]

        common_pairs_sorted = sorted(common_pairs)
        logger.info(f"Common pairs found: {common_pairs_sorted}")

        _cache_common_pairs = common_pairs_sorted
        _cache_timestamp = now

        return common_pairs_sorted
    except Exception as e:
        logger.error(f"Failed to fetch common pairs: {e}")
        return []