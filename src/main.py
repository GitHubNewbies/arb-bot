import os
import logging
from dotenv import load_dotenv
from src.database import get_session, create_all_tables
from src.engine import scan_market
from src.utils.pairs import get_common_usdc_pairs

def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("arb-bot")
    logger.info("🟢 Logging is set up.")

    session = get_session()
    create_all_tables(session)

    pairs = get_common_usdc_pairs()
    logger.info(f"📦 Common tradable USDC pairs: {pairs}")

    scan_market(pairs, session)

if __name__ == "__main__":
    main()
