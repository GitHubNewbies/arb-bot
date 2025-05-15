# db_inspector.py

from datetime import datetime, timedelta
from logger import get_logger
from src.db import SessionLocal
from src.models import Opportunity, ExecutedTrade, BotError

logger = get_logger("monitoring.db_inspector")

def check_recent_activity():
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        window = now - timedelta(minutes=10)

        opp_count = session.query(Opportunity).filter(Opportunity.timestamp > window).count()
        trade_count = session.query(ExecutedTrade).filter(ExecutedTrade.timestamp > window).count()
        error_count = session.query(BotError).filter(BotError.timestamp > window).count()

        logger.info(f"Recent activity (last 10 min): {opp_count} opportunities, {trade_count} trades, {error_count} errors")

        if error_count > 0:
            logger.warning("Recent errors detected in bot logs.")

    except Exception as e:
        logger.exception("Failed to check recent database activity")
    finally:
        session.close()
