# logger.py

import logging
import sys
import os
import threading
import traceback
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)

# Immediately initialize root logger so file handlers are attached early
logger = logging.getLogger("arb-bot")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler("logs/arb-bot.log", maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Global uncaught exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            f"Uncaught exception | Type: {exc_type.__name__} | Value: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        for handler in logger.handlers:
            handler.flush()

    sys.excepthook = handle_exception

    # Thread exception hook (Python 3.8+)
    if hasattr(threading, 'excepthook'):
        def thread_exception_handler(args):
            logger.critical(
                f"Uncaught thread exception | Type: {args.exc_type.__name__} | Value: {args.exc_value}",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
            )
            for handler in logger.handlers:
                handler.flush()
        threading.excepthook = thread_exception_handler


# Use this function in all modules (e.g. db.py, engine.py) to ensure consistent logging behavior
# Example: logger = get_logger(__name__)
def get_logger(name: str = "arb-bot", level: str = "INFO") -> logging.Logger:
    return logger
