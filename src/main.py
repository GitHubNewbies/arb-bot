import os
import logging
from dotenv import load_dotenv

from src.engine import scan_market
from src.db import ensure_tables_exist, get_session

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    logging.getLogger("arb-bot").info("Logging is set up.")

def get_env_pairs():
    raw = os.getenv("PAIRS", "")
    if not raw:
        logging.getLogger("arb-bot").warning("⚠️ No PAIRS found in .env. Defaulting to ETHUSDC,BTCUSDT,WIFUSDC.")
        return ["ETHUSDC", "BTCUSDT", "WIFUSDC"]
    return [pair.strip().upper() for pair in raw.split(",") if pair.strip()]

def main():
    load_dotenv()
    setup_logging()

    # Ensure DB schema is ready
    ensure_tables_exist()

    # Dynamically load trading pairs from .env
    pairs = get_env_pairs()

    # Create DB session
    session = get_session()

    try:
        # Run live market scan
        scan_market(pairs, session)
    finally:
        session.close()

if __name__ == "__main__":
    main()
