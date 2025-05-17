import os
import time
import hmac
import hashlib
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("arb-bot")

# Load from environment
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")


def validate_binance_credentials() -> bool:
    """Make a signed /account call to validate Binance keys."""
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        logger.error("❌ Binance API key/secret missing in environment.")
        return False

    try:
        timestamp = str(int(time.time() * 1000))
        query = f"recvWindow=5000&timestamp={timestamp}"
        signature = hmac.new(BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
        headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        logger.info("✅ Binance API credentials are valid.")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Binance credential check failed: {e.response.status_code} - {e.response.text}")
    except Exception as ex:
        logger.exception(f"❌ Binance credential validation error: {ex}")
    return False


def validate_bybit_credentials() -> bool:
    """Use /v5/account/wallet-balance to validate Bybit keys."""
    if not BYBIT_API_KEY or not BYBIT_API_SECRET:
        logger.error("❌ Bybit API key/secret missing in environment.")
        return False

    try:
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        endpoint = "/v5/account/wallet-balance"
        query_string = f"api_key={BYBIT_API_KEY}&timestamp={timestamp}&recvWindow={recv_window}"
        signature = hmac.new(
            BYBIT_API_SECRET.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

        url = f"https://api.bybit.com{endpoint}?{query_string}&sign={signature}"
        response = requests.get(url)
        json = response.json()

        if json.get("retCode") == 0:
            logger.info("✅ Bybit API credentials are valid.")
            return True
        else:
            logger.error(f"❌ Bybit credential check failed: {json.get('retCode')} - {json.get('retMsg')}")
    except Exception as ex:
        logger.exception(f"❌ Bybit credential validation error: {ex}")
    return False


def validate_all_credentials():
    """Run full credential validation for both exchanges."""
    logger.info("🔐 Running exchange credential checks...")
    binance_valid = validate_binance_credentials()
    bybit_valid = validate_bybit_credentials()

    if not binance_valid or not bybit_valid:
        raise EnvironmentError("❌ One or more exchange credentials are invalid. Check logs for details.")
    logger.info("✅ All exchange credentials validated successfully.")
