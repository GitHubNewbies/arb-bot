import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

from src.config import APP_ENV
from src.models import Base
from src.db import engine
from src.engine import scan_market


def init_db():
    print("[INIT] Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)


def main():
    print(f"[{APP_ENV.upper()}] Starting bot...")
    scan_market()


if __name__ == "__main__":
    init_db()
    main()
