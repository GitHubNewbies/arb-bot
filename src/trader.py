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
BYBIT_BASE = os.getenv("BYBIT_BASE", "https://api.bybit.com")
BINANCE_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET = os.getenv("BINANCE_SECRET")
BYBIT_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET = os.getenv("BYBIT_SECRET")

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
        logger.debug(f"[VALIDATION] Checking trade validity for {pair} (symbol: {symbol}) | qty={quantity}, price={price}")

        if self.exchange == "binance" and symbol in self.filters:
            try:
                filters = self.filters[symbol]
                notional_entry = next((f for f in filters if f['filterType'] in ['MIN_NOTIONAL', 'NOTIONAL']), None)
                if not notional_entry:
                    logger.warning(f"[FILTER] No notional filter found for {symbol}. Available filters: {[f['filterType'] for f in filters]}")
                    return False

                min_notional = float(notional_entry.get('minNotional') or notional_entry.get('minNotional', 0))
                notional = float(price) * float(quantity)
                logger.debug(f"[FILTER] Calculated notional: {notional:.4f}, Min required: {min_notional}")
                if notional < min_notional:
                    logger.warning(f"[FILTER] REJECTED: {pair} notional {notional:.4f} < required {min_notional}")
                    return False
            except Exception as e:
                logger.warning(f"[FILTER] Could not evaluate Binance filters for {symbol}: {e}")
                return False

        elif self.exchange == "bybit" and symbol in self.filters:
            try:
                min_qty = float(self.filters[symbol]['lotSizeFilter']['minOrderQty'])
                logger.debug(f"[FILTER] Bybit minimum quantity: {min_qty}, Proposed: {quantity}")
                if float(quantity) < min_qty:
                    logger.warning(f"[FILTER] REJECTED: {pair} quantity {quantity} < min required {min_qty}")
                    return False
            except Exception as e:
                logger.warning(f"[FILTER] Could not evaluate Bybit filters for {symbol}: {e}")
                return False

        logger.info(f"[VALIDATION] Trade accepted for {pair} | qty={quantity}, price={price}")
        return True

    def execute_trade(self, pair, side, quantity, price):
        logger.info(f"Preparing to execute trade: {side} {quantity} {pair} @ {price} on {self.exchange}")

        if not self.is_trade_valid(pair, quantity, price):
            logger.warning(f"[EXECUTION] Trade rejected after validation: {pair} | qty={quantity}, price={price}")
            return {"status": "filtered", "exchange": self.exchange, "pair": pair}

        if DRY_RUN:
            logger.info(f"[DRY_RUN] Simulated {side} {quantity} {pair} @ {price} on {self.exchange}")
            return {"status": "simulated", "exchange": self.exchange, "pair": pair}

        symbol = pair.replace("/", "")
        if self.exchange == "binance":
            if not EXECUTE_LIVE_ORDERS:
                return self.preview_binance_order(symbol, side, quantity, price)
            else:
                return self.binance_place_order(symbol, side, quantity, price)

        elif self.exchange == "bybit":
            if not EXECUTE_LIVE_ORDERS:
                return self.preview_bybit_order(symbol, side, quantity, price)
            else:
                return self.bybit_place_order(symbol, side, quantity, price)

        logger.warning(f"[EXECUTION] Unknown exchange: {self.exchange}. Cannot proceed with trade.")
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
