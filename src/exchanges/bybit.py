import os
import time
import hmac
import hashlib
from src.logger import get_logger
import requests
from decimal import Decimal
from typing import Dict, List, Optional, Any
from src.utils.auth import sign_request
from decimal import InvalidOperation

logger = get_logger(__name__, level="DEBUG")

class BybitAdapter:
    BASE_URL = "https://api.bybit.com"
    API_KEY = os.getenv("BYBIT_API_KEY")
    API_SECRET = os.getenv("BYBIT_API_SECRET")
    HEADERS = {}

    def __init__(self):
        self.symbol_map: Dict[str, str] = {}

    def _sign(self, params: Dict[str, Any]) -> str:
        query_string = "&".join(f"{key}={value}" for key, value in sorted(params.items()))
        return hmac.new(
            self.API_SECRET.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def get_tradable_pairs(self) -> List[str]:
        endpoint = "/v5/market/instruments-info"
        params = {"category": "linear"}
        try:
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
            if "result" in data and "list" in data["result"]:
                pairs = []
                for item in data["result"]["list"]:
                    if item["status"] == "Trading" and item["quoteCoin"].upper() == "USDC":
                        pair = f"{item['baseCoin'].upper()}/{item['quoteCoin'].upper()}"
                        pairs.append(pair)
                        self.symbol_map[pair] = item["symbol"]
                logger.info(f"✅ Bybit tradable USDC pairs fetched: {len(pairs)} pairs")
                return pairs
            return []
        except Exception as e:
            logger.error(f"❌ Failed to fetch Bybit pairs: {e}")
            return []

    def symbol_exists(self, symbol: str) -> bool:
        return symbol in self.symbol_map

    def fetch_price(self, symbol: str) -> Optional[Decimal]:
        try:
            formatted_symbol = self.symbol_map.get(symbol)
            if not formatted_symbol:
                fallback = symbol.replace("/", "")
                logger.warning(f"⚠️ Symbol not found in map for {symbol}, using fallback: {fallback}")
                formatted_symbol = fallback
            endpoint = "/v5/market/tickers"
            params = {"category": "linear", "symbol": formatted_symbol}
            logger.debug(f"📡 Requesting price from Bybit for {formatted_symbol} with params: {params}")
            response = requests.get(f"{self.BASE_URL}{endpoint}", params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("result", {}).get("list", [])
            if items and "lastPrice" in items[0]:
                price_str = items[0]["lastPrice"]
                logger.debug(f"📡 Raw price string from Bybit: {price_str} for symbol {symbol}")
                price_dec = Decimal(price_str).quantize(Decimal("0.00000001"))
                return price_dec
            logger.debug(f"📉 Bybit API returned no price for {formatted_symbol}, response: {data}")
            logger.warning(f"⚠️ No price data for {symbol} on Bybit. API response: {data}")
            return None
        except Exception as e:
            logger.error(f"❌ Bybit price fetch error for {symbol}: {e}")
            return None

    def get_balance(self, asset: str) -> Decimal:
        print("🧪 DEBUG: Entered get_balance() for BybitAdapter")
        try:
            logger.debug(f"📥 Requesting Bybit balance for {asset}")
            endpoint = "/v5/account/wallet-balance"
            method = "GET"
            clean_params = {"accountType": "UNIFIED"}

            headers, query_params = sign_request(endpoint, method, clean_params, exchange="bybit")
            url = f"{self.BASE_URL}{endpoint}"
            logger.debug(f"🚨 query_params keys: {list(query_params.keys())}")
            logger.debug(f"🚨 query_params full: {query_params}")
            logger.debug(f"🚨 Headers: {headers}")
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
            data = response.json()
            balances_list = data.get("result", {}).get("list", [])
            if not balances_list:
                logger.warning(f"⚠️ No balances found in Bybit response for asset {asset}. API response: {data}")
                return Decimal("0").quantize(Decimal("0.00000001"))
            for balance_info in balances_list:
                coin_balances = balance_info.get("coin", [])
                for coin in coin_balances:
                    if coin.get("coin", "").upper() == asset.upper():
                        balance_str = coin.get("availableToTrade", "0")
                        try:
                            balance = Decimal(balance_str).quantize(Decimal("0.00000001"))
                            logger.info(f"✅ Balance fetched for {asset}: {balance_str}")
                            return balance
                        except (InvalidOperation, TypeError) as err:
                            logger.error(f"❌ Invalid balance format for {asset}: {repr(balance_str)} | Error: {err}")
                            return Decimal("0").quantize(Decimal("0.00000001"))
            return Decimal("0").quantize(Decimal("0.00000001"))
        except Exception as e:
            logger.error(f"❌ Bybit balance fetch error for {asset}: {e}")
            return Decimal("0").quantize(Decimal("0.00000001"))

    def calculate_quantity(
        self,
        symbol: str,
        price: Decimal,
        side: str,
        balance: Optional[Decimal] = None,
        use_ratio: bool = True,
        quote_asset: Optional[str] = None,
        base_asset: Optional[str] = None,
        dry_run: bool = False
    ) -> Optional[Decimal]:
        import logging
        logger = logging.getLogger("arb-bot")

        if dry_run:
            logger.debug(f"[DRY-RUN] Would calculate quantity for {symbol} at price {price} with side {side}")
        try:
            quote_asset = quote_asset or "USDC"
            base_asset = base_asset or symbol.split("/")[0]

            if price is None or not isinstance(price, (Decimal, float, int, str)):
                logger.warning(f"⚠️ Invalid price for quantity calculation: {repr(price)} for {symbol}")
                return None
            try:
                price_val = Decimal(price)
                logger.debug(f"🔍 Converted price to Decimal: {price_val} for {symbol}")
            except (InvalidOperation, TypeError) as e:
                logger.error(f"❌ Failed to convert price to Decimal for {symbol}: {repr(price)} | Error: {e}")
                return None

            if balance is not None and isinstance(balance, str):
                try:
                    balance = Decimal(balance)
                except Exception as e:
                    logger.error(f"❌ Failed to convert balance string to Decimal for {symbol}: {repr(balance)} | Error: {e}")
                    return None

            logger.info(f"📊 Fetching balance for {quote_asset} to calculate quantity for {symbol} ({side.upper()})")
            if balance is None:
                balance = self.get_balance(quote_asset)
            if balance is None:
                logger.warning(f"⚠️ Unable to fetch balance for {quote_asset} in quantity calculation.")
                return None
            try:
                balance_val = Decimal(balance)
            except (InvalidOperation, TypeError) as e:
                logger.error(f"❌ Failed to convert balance to Decimal for {symbol}: {repr(balance)} | Error: {e}")
                return None

            allocation_ratio = Decimal(os.getenv("TRADE_ALLOCATION_RATIO", "1.0"))
            trade_buffer = Decimal(os.getenv("TRADE_BUFFER", "0"))
            max_trade_value = Decimal(os.getenv("MAX_TRADE_VALUE_USD", "0"))

            if use_ratio:
                usable_balance = balance_val * allocation_ratio - trade_buffer
                if max_trade_value > 0 and usable_balance > max_trade_value:
                    logger.info(f"🔒 Trade value capped from {usable_balance} to {max_trade_value}")
                    usable_balance = max_trade_value
            else:
                usable_balance = balance_val

            min_notional = Decimal("5")
            if usable_balance < min_notional:
                logger.warning(f"⚠️ Computed notional value too low for {symbol} | Value: {usable_balance}")
                return None

            quantity = usable_balance / price_val
            logger.info(f"✅ Quantity calculated for {symbol} | Qty: {quantity} | Price: {price_val} | Balance: {balance_val} | Usable: {usable_balance}")
            return quantity.quantize(Decimal("0.00000001"))
        except Exception as e:
            logger.error(f"❌ Error calculating quantity for {symbol}: {str(e)}")
            return None
