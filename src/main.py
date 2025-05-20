import logging
from src.utils.logging import setup_logging
from src.database import create_all_tables, get_db_session
from src.exchanges.discovery import get_common_pairs
from src.engine import scan_market
from src.exchanges.binance import BinanceAdapter
from src.exchanges.bybit import BybitAdapter

def main():
    setup_logging()
    logger = logging.getLogger("arb-bot")

    import os
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("🌍 Environment variables loaded.")

    try:
        logger.info("🟢 Logging is set up.")
        create_all_tables()

        pairs = get_common_pairs()
        if not pairs:
            logger.warning("⚠️ No common trading pairs found — exiting.")
            return

        session = get_db_session()
        logger.info(f"📊 Starting market scan for {len(pairs)} pairs")

        if not os.getenv("BINANCE_API_KEY") or not os.getenv("BINANCE_API_SECRET"):
            logger.error("❌ Binance API credentials not set. Exiting.")
            return
        if not os.getenv("BYBIT_API_KEY") or not os.getenv("BYBIT_API_SECRET"):
            logger.error("❌ Bybit API credentials not set. Exiting.")
            return

        binance = BinanceAdapter()
        logger.info("📡 Connected to Binance adapter.")
        bybit = BybitAdapter()
        logger.info("📡 Connected to Bybit adapter.")
        logger.info("🚀 Initiating market scan...")
        scan_market(pairs, session, binance, bybit)

    except Exception:
        logger.exception("❌ Unhandled error in main execution loop")

if __name__ == "__main__":
    main()
