# db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DATABASE_URL
from src.logger import get_logger

logger = get_logger("db")

try:
    engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine and session successfully initialized.")
except Exception as e:
    logger.exception("Failed to initialize database engine or session")
    raise
