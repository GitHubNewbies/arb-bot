import os
import time
import hmac
import hashlib
import requests
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")


class BybitAdapter:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.api_key = BYBIT_API_KEY
        self.api_secret = BYBIT_API_SECRET

    def _sign(self, params: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for Bybit API."""
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-BYBIT-API-KEY": self.api_key,
        }

    def fetch_tradable_pairs(self) -> List[str]:
        """Fetch tradable spot pairs from Bybit."""
        endpoint = "/v5/market/instruments-info"
        url = f"{self.base_url}{endpoint}"
        params = {
            "category": "spot"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            pairs = []
            if "result" in data and "list" in data["result"]:
                for item in data["result"]["list"]:
                    if item.get("status") == "Trading":
                        pairs.append(item["symbol"])  # e.g. "ETHUSDC"

            return pairs

        except Exception as e:
            logging.error(f"❌ Failed to fetch Bybit tradable pairs: {e}")
            return []

    def fetch_price(self, symbol: str) -> float:
        """Fetch current spot price for a symbol from Bybit v5"""
        endpoint = "/v5/market/tickers"
        url = f"{self.base_url}{endpoint}"
        market_symbol = symbol.replace("/", "")
        params = {
            "category": "spot",
            "symbol": market_symbol,
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "result" in data and "list" in data["result"] and data["result"]["list"]:
                return float(data["result"]["list"][0]["lastPrice"])

            logging.error(f"❌ Unexpected response format for {symbol}: {data}")
            return 0.0

        except Exception as e:
            logging.error(f"❌ Failed to fetch price for {symbol} on Bybit: {e}")
            return 0.0

    def calculate_quantity(self, balance: float, price: float, precision: int = 4) -> float:
        try:
            raw_qty = float(balance) / float(price)
            return round(raw_qty, precision)
        except Exception as e:
            logging.error(f"❌ Error calculating quantity: {e}")
            return 0.0
