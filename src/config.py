import os
import logging
import json

def get_pairs_to_monitor():
    try:
        pairs_env = os.getenv("PAIRS", "")
        pairs = [pair.strip().upper() for pair in pairs_env.split(",") if pair.strip()]
        logging.info(f"Loaded pairs: {pairs}")
        return pairs
    except Exception as e:
        logging.exception("Failed to load trading pairs.")
        raise

def get_price_lookup():
    try:
        raw = os.getenv("PRICE_LOOKUP", "{}")
        price_lookup = json.loads(raw)
        logging.info(f"Loaded price lookup: {price_lookup}")
        return price_lookup
    except Exception as e:
        logging.exception("Failed to load price lookup.")
        raise


def get_balance_safety_threshold():
    try:
        threshold = float(os.getenv("BALANCE_SAFETY_THRESHOLD", "0.95"))
        logging.info(f"Loaded balance safety threshold: {threshold}")
        return threshold
    except Exception as e:
        logging.exception("Failed to load balance safety threshold.")
        raise
