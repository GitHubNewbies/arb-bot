import os
import time
import hmac
import hashlib
import requests
import logging
from decimal import Decimal

BYBIT_BASE_URL = "https://api.bybit.com"
logger = logging.getLogger("arb-bot")

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")


class BybitAdapter:
    def fetch_price(self, pair: str) -> Decimal:
        """
        Fetches the current spot price for a given pair from Bybit.
        Input: 'SOL/USDC' ➜ matched as 'SOLUSDC' from ticker list.
        """
        url = f"{BYBIT_BASE_URL}/v5/market/tickers?category=spot"
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if data.get("retCode") != 0:
            raise ValueError(f"❌ Bybit API error: {data.get('retMsg', 'Unknown error')}")

        symbol = pair.replace("/", "")
        ticker_list = data["result"]["list"]
        match = next((t for t in ticker_list if t["symbol"] == symbol), None)

        if not match:
            raise ValueError(f"❌ No price data for {pair}")

        return Decimal(match["lastPrice"])

    def calculate_quantity(self, pair: str, price: Decimal, side: str) -> Decimal:
        """
        Fetches the USDC balance and calculates how much of the asset we can buy.
        Margin assumed available in Unified account.
        """
        endpoint = "/v5/account/wallet-balance"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"

        params = {
            "accountType": "UNIFIED",
            "timestamp": timestamp,
            "apiKey": BYBIT_API_KEY,
            "recvWindow": recv_window,
        }

        # Sign the parameters
        param_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(BYBIT_API_SECRET.encode(), param_string.encode(), hashlib.sha256).hexdigest()
        headers = {"Content-Type": "application/json"}
        params["sign"] = signature

        url = f"{BYBIT_BASE_URL}{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        balances = response.json()["result"]["list"][0]["coin"]

        usdc_entry = next((item for item in balances if item["coin"] == "USDC"), None)
        if not usdc_entry:
            raise ValueError("❌ No USDC balance found")

        free_balance = Decimal(usdc_entry["availableToWithdraw"])
        quantity = (free_balance / price).quantize(Decimal("0.000001"))

        if quantity <= 0:
            logger.warning(f"⚠️ Computed quantity too low for {pair} | Balance: {free_balance}, Price: {price}")
            return Decimal("0")

        return quantity

    def place_order(self, pair: str, quantity: Decimal, price: Decimal, side: str) -> dict:
        """
        Place a margin order via Bybit Unified account.
        """
        symbol = pair.replace("/", "")
        endpoint = "/v5/order/create"
        timestamp = str(int(time.time() * 1000))

        order = {
            "category": "linear",
            "symbol": symbol,
            "side": side.upper(),
            "orderType": "Limit",
            "qty": str(quantity),
            "price": str(price),
            "timeInForce": "GTC",
            "isLeverage": "1",
            "timestamp": timestamp,
            "apiKey": BYBIT_API_KEY,
        }

        param_string = "&".join(f"{k}={v}" for k, v in sorted(order.items()))
        signature = hmac.new(BYBIT_API_SECRET.encode(), param_string.encode(), hashlib.sha256).hexdigest()
        order["sign"] = signature

        headers = {"Content-Type": "application/json"}

        logger.info(f"[LIVE] Submitting Bybit order: {order}")
        response = requests.post(f"{BYBIT_BASE_URL}{endpoint}", json=order, headers=headers)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Bybit order failed: {response.text}")
            raise

        logger.info(f"✅ Bybit order placed: {response.json()}")
        return response.json()
