import os
import time
import hmac
import hashlib
import requests
import logging
from decimal import Decimal
from src.utils.auth import sign_request

logger = logging.getLogger("arb-bot")

BINANCE_BASE_URL = "https://api.binance.com"
BYBIT_BASE_URL = "https://api.bybit.com"

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

def _binance_order(symbol: str, side: str, quantity: Decimal, price: Decimal) -> None:
    assert side.upper() in ("BUY", "SELL"), f"❌ Invalid side: {side}"
    quantity = Decimal(quantity).normalize()
    price = Decimal(price).normalize()
    try:
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            raise EnvironmentError("❌ Binance API credentials missing")

        endpoint = "/api/v3/order"
        stripped_symbol = symbol.replace("/", "")

        params = {
            "symbol": stripped_symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": str(quantity),
            "price": str(price),
            "recvWindow": 5000,
        }

        logger.info(f"[LIVE] Placing {side.upper()} order on BINANCE for {symbol}: Qty={quantity}, Price={price}")

        headers, signed_params = sign_request(
            endpoint=endpoint,
            method="POST",
            api_key=BINANCE_API_KEY,
            api_secret=BINANCE_API_SECRET,
            params=params,
        )

        logger.info(f"[LIVE] Submitting order to Binance: {signed_params}")
        response = requests.post(BINANCE_BASE_URL + endpoint, headers=headers, params=signed_params)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"❌ Binance order failed with status {response.status_code}")
            try:
                logger.error(f"❌ Binance error response: {response.json()}")
            except Exception:
                logger.error(f"❌ Raw Binance error (non-JSON): {response.text}")
            raise http_err

        logger.info(f"✅ Binance order response: {response.json()}")

    except Exception as e:
        logger.exception("❌ Binance order submission failed")
        raise

def _bybit_order(symbol: str, side: str, quantity: Decimal, price: Decimal) -> None:
    assert side.upper() in ("BUY", "SELL"), f"❌ Invalid side: {side}"
    quantity = Decimal(quantity).normalize()
    price = Decimal(price).normalize()
    try:
        if not BYBIT_API_KEY or not BYBIT_API_SECRET:
            raise EnvironmentError("❌ Bybit API credentials missing")

        url = f"{BYBIT_BASE_URL}/v5/order/create"
        timestamp = str(int(time.time() * 1000))
        params = {
            "category": "linear",  # ✅ Use unified USDC margin trading (perpetual)
            "symbol": symbol,
            "side": side.upper(),
            "orderType": "Limit",
            "qty": str(quantity),
            "price": str(price),
            "timeInForce": "GTC",
            "apiKey": BYBIT_API_KEY,
            "timestamp": timestamp,
        }

        logger.info(f"[LIVE] Placing {side.upper()} order on BYBIT for {symbol}: Qty={quantity}, Price={price}")

        param_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(BYBIT_API_SECRET.encode(), param_string.encode(), hashlib.sha256).hexdigest()
        params["sign"] = signature

        headers = {
            "Content-Type": "application/json"
        }

        logger.info(f"[LIVE] Submitting order to Bybit: {params}")
        response = requests.post(url, headers=headers, json=params)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"❌ Bybit order failed with status {response.status_code}")
            try:
                logger.error(f"❌ Bybit error response: {response.json()}")
            except Exception:
                logger.error(f"❌ Raw Bybit error (non-JSON): {response.text}")
            raise http_err

        logger.info(f"✅ Bybit order response: {response.json()}")

    except Exception as e:
        logger.exception("❌ Bybit order submission failed")
        raise

def execute_order(exchange: str, symbol: str, side: str, quantity: Decimal, price: Decimal):
    if exchange.lower() == "binance":
        _binance_order(symbol, side, quantity, price)
    elif exchange.lower() == "bybit":
        _bybit_order(symbol, side, quantity, price)
    else:
        raise ValueError(f"Unsupported exchange: {exchange}")
