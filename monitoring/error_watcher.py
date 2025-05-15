# error_watcher.py

import logging
from datetime import datetime, timedelta
from logger import get_logger
from src.db import SessionLocal
from src.models import BotError

logger = get_logger("monitoring.error_watcher")


def find_recent_errors(window_minutes=30):
    session = SessionLocal()
    try:
        now = datetime.utcnow()
        window = now - timedelta(minutes=window_minutes)

        recent_errors = session.query(BotError).filter(BotError.timestamp > window).all()

        if recent_errors:
            logger.warning(f"Found {len(recent_errors)} errors in the last {window_minutes} minutes:")
            for err in recent_errors:
                logger.warning(f"[{err.timestamp}] {err.module}: {err.message}")
        else:
            logger.info("No recent errors found in database.")

    except Exception as e:
        logger.exception("Failed to scan for recent errors")
    finally:
        session.close()
