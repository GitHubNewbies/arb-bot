import os
import requests
from decimal import Decimal, ROUND_DOWN
import time
import hmac
import hashlib
import urllib.parse
import logging

BINANCE_BASE_URL = "https://api.binance.com"

class BinanceAdapter:
    def __init__(self):
        self._balance_cache = {}
        self.logger = logging.getLogger("arb-bot")

    def fetch_price(self, pair: str) -> Decimal:
        symbol = str(pair).replace("/", "").upper()
        url = f"{BINANCE_BASE_URL}/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return Decimal(response.json()["price"])

    def calculate_quantity(
        self,
        pair: str,
        price: Decimal,
        side: str,
        base_asset: str = "USDC",
        quote_asset: str = "USDC",
        use_ratio: bool = True,
        dry_run: bool = True
    ) -> Decimal:
        asset = base_asset
        self.logger.info(f"📊 Fetching {asset} balance to calculate quantity for {pair} ({side})")
        balance = self.get_balance(asset)

        if price <= 0:
            self.logger.warning(f"⚠️ Invalid price {price} for {pair}")
            return Decimal("0")

        TRADE_ALLOCATION_RATIO = Decimal("0.95")
        TRADE_BUFFER = Decimal("1.00")
        MAX_TRADE_VALUE_USD = Decimal("500")

        if use_ratio:
            safe_balance = (balance * TRADE_ALLOCATION_RATIO) - TRADE_BUFFER
            safe_balance = min(safe_balance, MAX_TRADE_VALUE_USD)
        else:
            safe_balance = balance

        if safe_balance <= 0:
            self.logger.warning(f"⚠️ Safe balance is too low after applying safety margins for {pair}")
            return Decimal("0")

        quantity = (safe_balance / price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        self.logger.info(f"✅ Binance quantity for {pair} ({side}) | Qty: {quantity} | Price: {price} | Balance: {balance}")

        if quantity <= 0:
            self.logger.warning(f"⚠️ Computed quantity too low for {pair} | Safe Balance: {safe_balance}, Price: {price}")
            return Decimal("0")

        return quantity

    def get_tradable_pairs(self) -> list[str]:
        url = f"{BINANCE_BASE_URL}/api/v3/exchangeInfo"
        response = requests.get(url)
        response.raise_for_status()
        symbols = response.json()["symbols"]
        return [
            f"{s['baseAsset']}/{s['quoteAsset']}"
            for s in symbols if s["status"] == "TRADING"
        ]

    def get_balance(self, asset: str) -> Decimal:
        if not isinstance(asset, str) or not asset.isalpha():
            self.logger.error(f"❌ Invalid asset requested for Binance balance: {asset}")
            return Decimal("0")

        if asset in self._balance_cache:
            return self._balance_cache[asset]

        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_secret:
            self.logger.error("❌ Binance API secret is missing.")
            return Decimal("0")

        endpoint = "/sapi/v1/margin/account"

        try:
            # Check server time drift for better signing
            binance_time_resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/time")
            binance_server_time = int(binance_time_resp.json()["serverTime"])
            local_time = int(time.time() * 1000)
            drift = abs(binance_server_time - local_time)
            if drift > 10000:
                self.logger.warning(f"⚠️ Local time drift from Binance server is {drift}ms, which may cause signature errors.")

            timestamp = binance_server_time
            recv_window = 5000
            params = {"recvWindow": recv_window, "timestamp": timestamp}
            query_string = urllib.parse.urlencode(sorted(params.items()))
            self.logger.debug(f"🧾 Binance query string to sign: {query_string}")

            signature = hmac.new(
                api_secret.encode("utf-8"),
                query_string.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()

            headers = {"X-MBX-APIKEY": api_key, "Content-Type": "application/x-www-form-urlencoded"}
            full_params = {**params, "signature": signature}
            debug_url = f"{BINANCE_BASE_URL}{endpoint}?{urllib.parse.urlencode(full_params)}"
            self.logger.debug(f"🌐 Full Binance request URL: {debug_url}")

            resp = requests.get(BINANCE_BASE_URL + endpoint, headers=headers, params=full_params)
            self.logger.debug(f"📉 Raw Binance margin response: {resp.text}")
            resp.raise_for_status()
            balances = resp.json().get("userAssets", [])
            balance_entry = next((b for b in balances if b["asset"] == asset.upper()), None)

            if not balance_entry:
                self.logger.warning(f"⚠️ No balance found for asset {asset}")
                return Decimal("0")

            free_balance = balance_entry.get("free", "")
            try:
                decimal_balance = Decimal(str(free_balance))
            except Exception as e:
                self.logger.error(f"❌ Invalid balance format received for {asset}: {free_balance} | Error: {e}")
                return Decimal("0")

            self.logger.info(f"💰 Binance cross margin balance for {asset}: {free_balance}")
            self._balance_cache[asset] = decimal_balance
            return decimal_balance
        except Exception as e:
            self.logger.error(f"❌ Binance balance fetch error for {asset}: {e}")
            return Decimal("0")