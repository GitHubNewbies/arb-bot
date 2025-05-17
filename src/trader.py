import os
import time
import hmac
import hashlib
import requests
import logging
from decimal import Decimal

logger = logging.getLogger("arb-bot")

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# 🔍 TEMP DEBUG: Print to confirm if environment variables are loading
print(f"🔍 DEBUG ENV CHECK: BINANCE_KEY={BINANCE_API_KEY} BINANCE_SECRET={BINANCE_API_SECRET} BYBIT_KEY={BYBIT_API_KEY} BYBIT_SECRET={BYBIT_API_SECRET}")

if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    logger.critical("❌ Binance API credentials are not set. Ensure BINANCE_API_KEY and BINANCE_API_SECRET are in environment.")
    raise EnvironmentError("Missing Binance API credentials")
if not BYBIT_API_KEY or not BYBIT_API_SECRET:
    logger.critical("❌ Bybit API credentials are not set. Ensure BYBIT_API_KEY and BYBIT_API_SECRET are in environment.")
    raise EnvironmentError("Missing Bybit API credentials")

logger.info("🔐 Loaded Binance and Bybit credentials successfully.")

def _sign_request(params: dict, secret: str) -> str:
    query_string = "&".join([f"{key}={params[key]}" for key in sorted(params)])
    return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

def _binance_order(symbol: str, side: str, quantity: Decimal, price: float):
    url = "https://api.binance.com/api/v3/order"
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "timeInForce": "GTC",
        "quantity": str(quantity),
        "price": str(price),
        "recvWindow": 5000,
        "timestamp": timestamp,
    }
    signature = _sign_request(params, BINANCE_API_SECRET)
    params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY,
    }

    logger.info(f"[LIVE] Submitting order to Binance: {params}")

    response = requests.post(url, headers=headers, params=params)

    try:
        response.raise_for_status()
        logger.info("✅ Order successfully submitted to Binance.")
    except requests.HTTPError as e:
        logger.error("❌ Binance order failed with status %s", response.status_code)
        try:
            error_json = response.json()
            logger.error("❌ Binance error body: %s", error_json)
        except Exception:
            logger.warning("⚠️ Failed to parse Binance error response JSON")
        raise

def _bybit_order(symbol: str, side: str, quantity: Decimal, price: float):
    url = "https://api.bybit.com/v5/order/create"
    timestamp = str(int(time.time() * 1000))
    params = {
        "category": "spot",
        "symbol": symbol,
        "side": side.upper(),
        "orderType": "LIMIT",
        "qty": str(quantity),
        "price": str(price),
        "timeInForce": "GTC",
        "timestamp": timestamp,
        "apiKey": BYBIT_API_KEY,
    }
    # Build signature
    param_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    signature = hmac.new(BYBIT_API_SECRET.encode('utf-8'), param_string.encode('utf-8'), hashlib.sha256).hexdigest()
    params["sign"] = signature

    headers = {
        "Content-Type": "application/json"
    }

    logger.info(f"[LIVE] Submitting order to Bybit: {params}")

    response = requests.post(url, headers=headers, json=params)

    try:
        response.raise_for_status()
        logger.info("✅ Order successfully submitted to Bybit.")
    except requests.HTTPError as e:
        logger.error("❌ Bybit order failed with status %s", response.status_code)
        try:
            error_json = response.json()
            logger.error("❌ Bybit error body: %s", error_json)
        except Exception:
            logger.warning("⚠️ Failed to parse Bybit error response JSON")
        raise

def execute_order(exchange: str, symbol: str, side: str, quantity: Decimal, price: float):
    if exchange.lower() == "binance":
        _binance_order(symbol, side, quantity, price)
    elif exchange.lower() == "bybit":
        _bybit_order(symbol, side, quantity, price)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")
