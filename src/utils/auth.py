import hmac
import hashlib
import time
import os
from typing import Tuple
import logging
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("arb-bot")


def sign_request(
    endpoint: str,
    method: str,
    params: dict,
    api_key: str = None,
    api_secret: str = None,
    exchange: str = "binance"
) -> Tuple[dict, dict]:
    """
    Generate headers and signed query params for Binance or Bybit requests.
    """
    logger.debug(f"📥 sign_request() called with endpoint: {endpoint}, method: {method}, params: {params}")
    params = deepcopy(params)
    exchange = exchange.lower()
    if exchange == "bybit":
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        if not api_key:
            raise ValueError("❌ BYBIT_API_KEY is missing.")
    elif exchange == "binance":
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")

    if not api_key or not api_secret:
        raise ValueError(f"Missing {exchange.title()} API credentials")

    timestamp = int(time.time() * 1000)
    recv_window = 5000
    signed_params = dict(params)
    signed_params["timestamp"] = timestamp
    signed_params["recvWindow"] = recv_window

    if not api_key or len(api_key.strip()) < 30:
        logger.error(f"❌ API key seems invalid or empty: {repr(api_key)}")
    else:
        logger.debug(f"✅ API key loaded: {api_key[:6]}... (length={len(api_key.strip())})")

    if not api_secret or len(api_secret.strip()) < 30:
        logger.error("❌ API secret is missing or malformed.")
    else:
        logger.debug("✅ API secret loaded and appears valid.")

    # Determine if this is a Bybit request by checking the exchange parameter
    if exchange.lower() == "bybit":
        # Remove auth-related fields from params
        account_params = {k: v for k, v in params.items() if k == "accountType"}

        # Prepare query string for signature (must include auth fields)
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        sign_string = f"{timestamp}{api_key}{recv_window}{query_string}"
        signature = hmac.new(api_secret.encode(), sign_string.encode(), hashlib.sha256).hexdigest()

        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": str(recv_window),
            "Content-Type": "application/json"
        }
        logger.debug(f"🔍 sign_request() returning headers: {headers}")
        logger.debug(f"🔍 sign_request() returning query_params: {account_params}")
        return headers, account_params
    else:
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(signed_params.items())])
        signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

        signed_params["signature"] = signature

        headers = {
            "X-MBX-APIKEY": api_key
        }
        logger.debug(f"🔑 Binance query string to sign: {query_string}")
        logger.debug(f"🧾 Binance HMAC signature: {signature}")
        logger.debug(f"📦 Final signed params sent: {signed_params}")
        logger.debug(f"🔍 sign_request() returning headers: {headers}")
        logger.debug(f"🔍 sign_request() returning query_params: {signed_params}")

        return headers, signed_params
