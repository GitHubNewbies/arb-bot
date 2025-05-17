import hmac
import hashlib
import time
import os
from typing import Tuple

def sign_request(
    endpoint: str,
    method: str,
    params: dict,
    api_key: str = None,
    api_secret: str = None
) -> Tuple[dict, dict]:
    """
    Generate headers and signed query params for Binance requests.
    """
    api_key = api_key or os.getenv("BINANCE_API_KEY")
    api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("Missing Binance API credentials")

    timestamp = int(time.time() * 1000)
    params["timestamp"] = timestamp
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    signed_params = dict(params)
    signed_params["signature"] = signature

    headers = {
        "X-MBX-APIKEY": api_key
    }

    return headers, signed_params
