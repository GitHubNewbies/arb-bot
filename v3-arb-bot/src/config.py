import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL         = os.getenv("DATABASE_URL")
SQLITE_DB_PATH       = os.getenv("SQLITE_DB_PATH", "data/trades.db")

PAIRS                = os.getenv("PAIR", "SOL/USDC").split(",")
SPREAD_THRESHOLD     = float(os.getenv("SPREAD_THRESHOLD", "0.004"))
TRADE_SIZE           = float(os.getenv("TRADE_SIZE", "1"))
DESIRED_NOTIONAL_USD = float(os.getenv("DESIRED_NOTIONAL_USD", "0"))
DRY_RUN              = os.getenv("DRY_RUN", "True").lower() == "true"
COOLDOWN_SECONDS     = 60

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET  = os.getenv("BINANCE_SECRET")
BYBIT_API_KEY   = os.getenv("BYBIT_API_KEY")
BYBIT_SECRET    = os.getenv("BYBIT_SECRET")

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID   = os.getenv("TG_CHAT_ID")