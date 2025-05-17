import logging
from src.engine import scan_market
from src.db import ensure_tables_exist, get_session

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    logging.getLogger("arb-bot").info("Logging is set up.")

def main():
    setup_logging()

    # Ensure DB schema is ready
    ensure_tables_exist()

    # Define trading pairs
    pairs = ["ETHUSDC", "BTCUSDT", "WIFUSDC"]

    # Create DB session
    session = get_session()

    try:
        # Run live market scan
        scan_market(pairs, session)
    finally:
        session.close()

if __name__ == "__main__":
    main()
