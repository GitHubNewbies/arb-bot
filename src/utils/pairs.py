import requests
import logging

logger = logging.getLogger("arb-bot")

def fetch_usdc_pairs_binance():
    resp = requests.get("https://api.binance.com/api/v3/exchangeInfo")
    resp.raise_for_status()
    data = resp.json()
    return {s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDC' and s['status'] == 'TRADING'}

def fetch_usdc_pairs_bybit():
    resp = requests.get("https://api.bybit.com/v5/market/instruments-info?category=spot")
    resp.raise_for_status()
    data = resp.json()
    return {s['symbol'].replace('-', '') for s in data['result']['list'] if s['symbol'].endswith("USDC")}

def get_common_usdc_pairs():
    try:
        binance_pairs = fetch_usdc_pairs_binance()
        bybit_pairs = fetch_usdc_pairs_bybit()
        common = binance_pairs.intersection(bybit_pairs)
        formatted = [f"{s.replace('USDC','')}/USDC" for s in common]
        return sorted(formatted)
    except Exception as e:
        logger.error(f"❌ Failed to fetch common pairs: {e}")
        return []
