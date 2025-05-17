import os
import requests
import logging
from decimal import Decimal, ROUND_DOWN
from src.utils.auth import sign_request

logger = logging.getLogger("arb-bot")
BINANCE_BASE_URL = "https://api.binance.com"

class BinanceAdapter:
    def fetch_price(self, pair: str) -> Decimal:
        symbol = pair.replace("/", "")
        url = f"{BINANCE_BASE_URL}/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return Decimal(response.json()["price"])

    def calculate_quantity(self, pair: str, price: Decimal, side: str) -> Decimal:
        symbol = pair.replace("/", "")
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        endpoint = "/sapi/v1/margin/account"

        headers, signed_params = sign_request(
            endpoint=endpoint,
            method="GET",
            api_key=api_key,
            api_secret=api_secret,
            params={}
        )

        response = requests.get(BINANCE_BASE_URL + endpoint, headers=headers, params=signed_params)
        response.raise_for_status()

        balances = response.json().get("userAssets", [])
        asset = symbol.replace("USDC", "") if side == "BUY" else "USDC"
        entry = next((b for b in balances if b["asset"] == asset), None)

        if not entry:
            raise ValueError(f"❌ No margin balance for asset {asset}")

        free_balance = Decimal(entry["free"])
        quantity = (free_balance / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        if quantity <= 0:
            logger.warning(f"⚠️ Computed quantity too low for {pair} | Balance: {free_balance}, Price: {price}")
            return Decimal("0")

        return quantity

    def place_order(self, pair: str, quantity: Decimal, price: Decimal, side: str) -> dict:
        symbol = pair.replace("/", "")
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        endpoint = "/sapi/v1/margin/order"

        params = {
            "symbol": symbol,
            "side": side.upper(),
            "type": "LIMIT",
            "timeInForce": "GTC",
            "quantity": str(quantity.normalize()),
            "price": str(price.normalize()),
            "recvWindow": 5000,
        }

        headers, signed_params = sign_request(
            endpoint=endpoint,
            method="POST",
            api_key=api_key,
            api_secret=api_secret,
            params=params,
        )

        logger.info(f"[LIVE] Submitting margin order to Binance: {signed_params}")
        response = requests.post(BINANCE_BASE_URL + endpoint, headers=headers, params=signed_params)

        try:
            response.raise_for_status()
            logger.info(f"✅ Binance order placed: {response.json()}")
            return response.json()
        except requests.RequestException:
            logger.error(f"❌ Binance error: {response.status_code} - {response.text}")
            raise
