import os
import time
import hmac
import hashlib
import requests
import logging
from decimal import Decimal, ROUND_DOWN

logger = logging.getLogger("arb-bot")
BYBIT_BASE_URL = "https://api.bybit.com"

class BybitAdapter:
    def fetch_price(self, pair: str) -> Decimal:
        symbol = pair.replace("/", "")
        url = f"{BYBIT_BASE_URL}/v5/market/tickers?category=linear&symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        tickers = response.json().get("result", {}).get("list", [])
        if not tickers:
            raise ValueError(f"❌ No price data for {symbol}")
        return Decimal(tickers[0]["lastPrice"])

    def calculate_quantity(self, pair: str, price: Decimal, side: str) -> Decimal:
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        symbol = pair.replace("/", "")
        url = f"{BYBIT_BASE_URL}/v5/account/wallet-balance?accountType=UNIFIED"
        timestamp = str(int(time.time() * 1000))

        params = {"apiKey": api_key, "timestamp": timestamp}
        query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()

        headers = {"X-BAPI-API-KEY": api_key, "X-BAPI-SIGN": signature, "X-BAPI-TIMESTAMP": timestamp}
        response = requests.get(url, headers=headers, params={})
        response.raise_for_status()

        balances = response.json()["result"]["list"][0]["coin"]
        asset = symbol.replace("USDC", "") if side == "BUY" else "USDC"
        entry = next((c for c in balances if c["coin"] == asset), None)

        if not entry:
            raise ValueError(f"❌ No Bybit balance for {asset}")

        free = Decimal(entry["availableToWithdraw"])
        quantity = (free / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        if quantity <= 0:
            logger.warning(f"⚠️ Computed quantity too low for {pair} | Balance: {free}, Price: {price}")
            return Decimal("0")

        return quantity

    def place_order(self, pair: str, quantity: Decimal, price: Decimal, side: str) -> dict:
        api_key = os.getenv("BYBIT_API_KEY")
        api_secret = os.getenv("BYBIT_API_SECRET")
        symbol = pair.replace("/", "")
        endpoint = "/v5/order/create"
        url = BYBIT_BASE_URL + endpoint

        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.upper(),
            "orderType": "Limit",
            "qty": str(quantity),
            "price": str(price),
            "timeInForce": "GTC",
        }

        timestamp = str(int(time.time() * 1000))
        params_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signed_str = f"{timestamp}{api_key}5000{params_str}"
        signature = hmac.new(api_secret.encode(), signed_str.encode(), hashlib.sha256).hexdigest()

        headers = {
            "X-BAPI-API-KEY": api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-SIGN": signature,
            "Content-Type": "application/json",
        }

        logger.info(f"[LIVE] Submitting order to Bybit: {params}")
        response = requests.post(url, headers=headers, json=params)

        try:
            response.raise_for_status()
            logger.info(f"✅ Bybit order placed: {response.json()}")
            return response.json()
        except requests.RequestException:
            logger.error(f"❌ Bybit order failed: {response.status_code} - {response.text}")
            raise
