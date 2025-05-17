import os
import time
import hmac
import hashlib
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

if not BYBIT_API_KEY or not BYBIT_API_SECRET:
    raise EnvironmentError("❌ Missing Bybit API credentials. Check .env or environment variables.")

def fetch_bybit_price(pair: str) -> Decimal:
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={pair}"
    response = requests.get(url)
    response.raise_for_status()

    tickers = response.json().get("result", {}).get("list", [])
    if not tickers:
        raise ValueError(f"No ticker data found for {pair} on Bybit.")
    
    return Decimal(tickers[0]["lastPrice"])


def calculate_bybit_quantity(pair: str, price: Decimal, side: str) -> Decimal:
    endpoint = "/v5/account/wallet-balance"
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    query = f"accountType=UNIFIED&api_key={BYBIT_API_KEY}&recvWindow={recv_window}&timestamp={timestamp}"
    signature = hmac.new(
        BYBIT_API_SECRET.encode(),
        query.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f"https://api.bybit.com{endpoint}?{query}&sign={signature}"
    headers = {"X-BYBIT-API-KEY": BYBIT_API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    json_data = response.json()

    # 🪵 Optional debug
    print("[DEBUG] Bybit wallet response:", json_data)

    result = json_data.get("result", {})
    wallet_list = result.get("list", [])

    if not wallet_list:
        raise ValueError("❌ Bybit wallet response missing or empty. Check API permissions or account status.")

    coins = wallet_list[0].get("coin", [])
    asset = pair.replace("USDT", "") if side == "SELL" else "USDT"

    asset_data = next((c for c in coins if c["coin"] == asset), None)
    if not asset_data:
        raise ValueError(f"❌ Asset {asset} not found in wallet.")

    available = Decimal(asset_data["availableToWithdraw"])

    if side == "BUY":
        return (available / price).quantize(Decimal("0.0001"))
    else:
        return available.quantize(Decimal("0.0001"))
