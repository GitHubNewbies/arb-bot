import os
import time
import hmac
import hashlib
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise EnvironmentError("❌ Missing Binance API credentials. Check .env or environment variables.")

def fetch_binance_price(pair: str) -> Decimal:
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    response = requests.get(url)
    response.raise_for_status()
    return Decimal(response.json()["price"])

def get_binance_precision(pair: str) -> int:
    url = "https://api.binance.com/api/v3/exchangeInfo"
    response = requests.get(url)
    response.raise_for_status()
    symbols = response.json()["symbols"]
    for s in symbols:
        if s["symbol"] == pair:
            for f in s["filters"]:
                if f["filterType"] == "LOT_SIZE":
                    step_size = Decimal(f["stepSize"])
                    return abs(step_size.as_tuple().exponent)
    raise ValueError(f"❌ Could not determine precision for {pair}")

def calculate_binance_quantity(pair: str, price: Decimal, side: str) -> Decimal:
    timestamp = str(int(time.time() * 1000))
    query = f"recvWindow=5000&timestamp={timestamp}"
    signature = hmac.new(BINANCE_API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

    url = f"https://api.binance.com/api/v3/account?{query}&signature={signature}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    balances = resp.json().get("balances", [])
    asset = pair.replace("USDT", "").replace("USDC", "") if side == "BUY" else "USDT"
    asset_balance = next((b for b in balances if b["asset"] == asset), None)
    available = Decimal(asset_balance["free"]) if asset_balance else Decimal("0")

    precision = get_binance_precision(pair)
    if side == "BUY":
        qty = available / price
    else:
        qty = available

    return qty.quantize(Decimal(f"1e-{precision}"))
