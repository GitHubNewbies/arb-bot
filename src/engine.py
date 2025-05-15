# engine.py

from datetime import datetime
from src.db import SessionLocal
from src.models import Opportunity
from src.config import APP_ENV
from src.logger import get_logger
from src.trader import TradeExecutor

logger = get_logger(__name__)

def scan_market():
    session = SessionLocal()
    executor = TradeExecutor("binance")

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
        logger.info(f"[{APP_ENV.upper()}] Opportunity logged: {opp.pair} @ {opp.spread_pct}%")

        # Execute trade after logging opportunity
        executor.execute_trade(
            pair=opp.pair,
            side="buy",
            quantity=1.5,
            price=opp.buy_price
        )

    except Exception as e:
        logger.exception("[ERROR] Failed to log dry-run opportunity or execute trade")
        session.rollback()
    finally:
        try:
            session.close()
        except Exception as e:
            logger.exception("[ERROR] Failed to close DB session")
