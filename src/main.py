import logging
from src.utils.logging import setup_logging
from src.database import create_all_tables, get_db_session
from src.exchanges.discovery import get_common_pairs
from src.engine import scan_market

def main():
    setup_logging()
    logger = logging.getLogger("arb-bot")

    try:
        logger.info("🟢 Logging is set up.")
        create_all_tables()

        pairs = get_common_pairs()
        if not pairs:
            logger.warning("⚠️ No common trading pairs found — exiting.")
            return

        session = get_db_session()
        logger.info(f"📊 Starting market scan for {len(pairs)} pairs")
        scan_market(pairs, session)

    except Exception as e:
        logger.exception("❌ Unhandled error in main execution loop")

if __name__ == "__main__":
    main()
