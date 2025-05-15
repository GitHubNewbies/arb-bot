# trader.py

import os
import time
import requests
import hmac
import hashlib
from urllib.parse import urlencode
from src.logger import get_logger

logger = get_logger(__name__)

DRY_RUN = os.getenv("DRY_RUN", "True").lower() == "true"
EXECUTE_LIVE_ORDERS = os.getenv("EXECUTE_LIVE_ORDERS", "False").lower() == "true"
BINANCE_BASE = "https://api.binance.com"
BYBIT_BASE = "https://api.bybit.com"
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")

class TradeExecutor:
    def __init__(self, exchange_name):
        self.exchange = exchange_name.lower()
        self.filters = {}
        logger.info(f"TradeExecutor initialized for {exchange_name} | DRY_RUN={DRY_RUN} | EXECUTE_LIVE_ORDERS={EXECUTE_LIVE_ORDERS}")
        self.load_filters()

    def load_filters(self):
        try:
            if self.exchange == "binance":
                r = requests.get(f"{BINANCE_BASE}/api/v3/exchangeInfo")
                data = r.json()
                self.filters = {
                    s['symbol']: s['filters'] for s in data['symbols']
                }
                logger.info("[BINANCE] Exchange info loaded.")
            elif self.exchange == "bybit":
                r = requests.get(f"{BYBIT_BASE}/v5/market/instruments-info?category=spot")
                data = r.json()
                self.filters = {
                    i['symbol']: i for i in data['result']['list']
                }
                logger.info("[BYBIT] Market info loaded.")
        except Exception as e:
            logger.exception(f"[ERROR] Failed to fetch exchange info for {self.exchange}")

    def is_trade_valid(self, pair, quantity, price):
        symbol = pair.replace("/", "")
        if self.exchange == "binance" and symbol in self.filters:
            try:
                filters = self.filters[symbol]
                notional_entry = next((f for f in filters if f['filterType'] in ['MIN_NOTIONAL', 'NOTIONAL']), None)
                if not notional_entry:
                    logger.warning(f"[FILTER] No notional filter found for {symbol}. Available: {[f['filterType'] for f in filters]}")
                    return False

                min_notional = float(notional_entry.get('minNotional') or notional_entry.get('minNotional', 0))
                notional = float(price) * float(quantity)
                if notional < min_notional:
                    logger.warning(f"[FILTER] {pair} notional {notional:.4f} < {min_notional}")
                    return False
            except Exception as e:
                logger.warning(f"[FILTER] Could not evaluate filters for {symbol}: {e}")
                return False

        elif self.exchange == "bybit" and symbol in self.filters:
            try:
                min_qty = float(self.filters[symbol]['lotSizeFilter']['minOrderQty'])
                if float(quantity) < min_qty:
                    logger.warning(f"[FILTER] {pair} quantity {quantity} < min {min_qty}")
                    return False
            except Exception as e:
                logger.warning(f"[FILTER] Could not evaluate filters for {symbol}: {e}")
                return False

        return True

    def execute_trade(self, pair, side, quantity, price):
        logger.info(f"Preparing to execute trade: {side} {quantity} {pair} @ {price} on {self.exchange}")

        if not self.is_trade_valid(pair, quantity, price):
            logger.warning(f"[SKIPPED] Trade rejected due to filters: {pair} {quantity} @ {price}")
            return {"status": "filtered", "exchange": self.exchange, "pair": pair}

        if DRY_RUN:
            logger.info(f"[DRY_RUN] Simulated {side} {quantity} {pair} @ {price} on {self.exchange}")
            return {"status": "simulated", "exchange": self.exchange, "pair": pair}

        if self.exchange == "binance":
            if not EXECUTE_LIVE_ORDERS:
                return self.preview_binance_order(pair.replace("/", ""), side, quantity, price)
            else:
                return self.binance_place_order(pair.replace("/", ""), side, quantity, price)

        logger.warning("[SKIPPED] Live trading only implemented for Binance so far.")
        return {"status": "skipped", "exchange": self.exchange, "pair": pair}

    def preview_binance_order(self, symbol, side, quantity, price):
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "LIMIT",
                "timeInForce": "GTC",
                "quantity": quantity,
                "price": price,
                "recvWindow": 5000,
                "timestamp": timestamp
            }
            query_string = urlencode(params)
            signature = hmac.new(BINANCE_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            params["signature"] = signature
            logger.info(f"[PREVIEW] Binance order prepared: {params}")
            logger.info(f"[PREVIEW] If EXECUTE_LIVE_ORDERS=True, this order would now be submitted to Binance.")
            return {"status": "previewed", "params": params}
        except Exception as e:
            logger.exception(f"[ERROR] Failed to prepare Binance order for {symbol}")
            return {"status": "error", "reason": str(e)}

    def binance_place_order(self, symbol, side, quantity, price):
        try:
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "side": side.upper(),
                "type": "LIMIT",
                "timeInForce": "GTC",
                "quantity": quantity,
                "price": price,
                "recvWindow": 5000,
                "timestamp": timestamp
            }
            query_string = urlencode(params)
            signature = hmac.new(BINANCE_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            params["signature"] = signature
            headers = {"X-MBX-APIKEY": BINANCE_KEY}

            res = requests.post(f"{BINANCE_BASE}/api/v3/order", headers=headers, params=params)
            res.raise_for_status()
            logger.info(f"[LIVE] Binance order successful: {res.json()}")
            return {"status": "executed", "response": res.json()}

        except Exception as e:
            logger.exception(f"[ERROR] Binance trade failed for {symbol}")
            return {"status": "error", "reason": str(e)}
