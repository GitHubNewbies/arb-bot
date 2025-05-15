from datetime import datetime
from src.db import SessionLocal
from src.models import Opportunity
from src.config import APP_ENV


def scan_market():
    session = SessionLocal()
    try:
        opp = Opportunity(
            timestamp=datetime.utcnow(),
            pair="ETH/USDC",
            buy_exchange="binance",
            sell_exchange="bybit",
            buy_price=1850.00,
            sell_price=1865.00,
            spread_pct=0.81,
            notional=50.0,
            reason_skipped="dry_run",
            meta={"simulated": True}
        )
        session.add(opp)
        session.commit()
        print(f"[{APP_ENV.upper()}] Logged dry-run opportunity.")
    except Exception as e:
        print(f"[ERROR] Failed to log: {e}")
        session.rollback()
    finally:
        session.close()
