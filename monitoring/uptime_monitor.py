# uptime_monitor.py

import os
import time
import logging
from logger import get_logger

logger = get_logger("monitoring.uptime")

HEARTBEAT_FILE = "logs/arb-bot.heartbeat"
HEARTBEAT_INTERVAL = 600  # 10 minutes


def check_heartbeat():
    try:
        if not os.path.exists(HEARTBEAT_FILE):
            logger.warning("No heartbeat file found. Bot may not have started.")
            return

        last_modified = os.path.getmtime(HEARTBEAT_FILE)
        age = time.time() - last_modified

        if age > HEARTBEAT_INTERVAL:
            logger.error(f"Heartbeat stale: last updated {age:.0f} seconds ago.")
        else:
            logger.info("Bot heartbeat is healthy.")

    except Exception as e:
        logger.exception("Error checking heartbeat status")
