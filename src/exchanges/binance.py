import os
import requests
from decimal import Decimal, ROUND_DOWN
from src.utils.auth import sign_request

BINANCE_BASE_URL = "https://api.binance.com"

class BinanceAdapter:
    def fetch_price(self, pair: str) -> Decimal:
        symbol = pair.replace("/", "").upper()
        url = f"{BINANCE_BASE_URL}/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return Decimal(response.json()["price"])

    def calculate_quantity(self, pair: str, price: Decimal, side: str) -> Decimal:
        import logging

        logger = logging.getLogger("arb-bot")
        symbol = pair.replace("/", "").upper()
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        endpoint = "/api/v3/account"

        headers, signed_params = sign_request(
            endpoint=endpoint,
            method="GET",
            api_key=api_key,
            api_secret=api_secret,
            params={}
        )

        resp = requests.get(BINANCE_BASE_URL + endpoint, headers=headers, params=signed_params)
        resp.raise_for_status()
        balances = resp.json().get("balances", [])

        asset = symbol.replace("USDC", "") if side.upper() == "BUY" else "USDC"
        balance_entry = next((b for b in balances if b["asset"] == asset), None)

        if not balance_entry:
            raise ValueError(f"❌ No balance found for asset {asset}")

        balance = Decimal(balance_entry["free"])
        quantity = (balance / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        if quantity <= 0:
            logger.warning(f"⚠️ Computed quantity too low for {pair} | Balance: {balance}, Price: {price}")
            return Decimal("0")

        return quantity

    def fetch_tradable_pairs(self) -> list[str]:
        url = f"{BINANCE_BASE_URL}/api/v3/exchangeInfo"
        response = requests.get(url)
        response.raise_for_status()

        symbols = response.json()["symbols"]
        return [
            f"{s['baseAsset']}/{s['quoteAsset']}"
            for s in symbols
            if s["status"] == "TRADING"
        ]
