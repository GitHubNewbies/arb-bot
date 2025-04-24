import os, socket, sys, subprocess, requests
import ccxt
from .config import PAIRS, SPREAD_THRESHOLD, TG_BOT_TOKEN, TG_CHAT_ID

API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"

def get_dependencies():
    try:
        out = subprocess.check_output([sys.executable, "-m", "pip", "freeze"])
        return out.decode().splitlines()
    except:
        return ["❌ failed to fetch deps"]

def send_startup_alert():
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return

    hostname = socket.gethostname()
    pyver    = sys.version.replace("\n", " ")
    deps     = get_dependencies()
    snippet  = "\n".join(deps[:10] + (["…"] if len(deps)>10 else []))
    ccxt_ver = ccxt.__version__
    bin_ver  = getattr(ccxt.binance(), "version", "n/a")
    byb_ver  = getattr(ccxt.bybit(),   "version", "n/a")

    text = (
        f"*🚀 Bot Deployed!*\n"
        f"`Host:` {hostname}\n"
        f"`Python:` {pyver}\n"
        f"`CCXT:` {ccxt_ver} BinanceAPI:{bin_ver} BybitAPI:{byb_ver}\n"
        f"`Pairs:` {','.join(PAIRS)}\n"
        f"`Threshold:` {SPREAD_THRESHOLD*100:.2f}%\n\n"
        f"*Top deps:*\n```{snippet}```"
    )
    requests.post(API_URL, json={
        "chat_id":    TG_CHAT_ID,
        "text":       text,
        "parse_mode": "Markdown"
    })
