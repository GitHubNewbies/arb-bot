# src/database.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models import Base, TradeLog, OpportunityLog  # Import models and shared Base
from sqlalchemy.exc import SQLAlchemyError
import logging
from decimal import Decimal
logger = logging.getLogger("arb-bot")

# Pull the connection string from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create SQLAlchemy engine and session factory
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

def get_db_session() -> Session:
    """Returns a new SQLAlchemy session."""
    logger.debug("Creating new database session")
    return SessionLocal()

def create_all_tables():
    """Creates all tables defined by SQLAlchemy models."""
    logger.info("Creating all database tables...")
    Base.metadata.create_all(bind=engine)


def log_opportunity_safe(session: Session, opportunity_data: dict):
    """Logs an arbitrage opportunity to the database with error handling."""
    required_fields = ["pair", "spread", "timestamp"]
    if not all(field in opportunity_data for field in required_fields):
        logger.warning(f"Missing required fields in opportunity data: {opportunity_data}")
        return
    try:
        opportunity = OpportunityLog(**opportunity_data)
        session.add(opportunity)
        session.commit()
        logger.info(f"Logged opportunity: {opportunity}")
    except SQLAlchemyError as e:
        logger.error(f"Failed to log opportunity: {e}")
        session.rollback()

def log_trade_safe(session: Session, trade_data: dict):
    """Logs a trade execution to the database with error handling."""
    required_fields = ["pair", "exchange", "side", "quantity", "price", "timestamp"]
    if not all(field in trade_data for field in required_fields):
        logger.warning(f"Missing required fields in trade data: {trade_data}")
        return
    try:
        trade = TradeLog(**trade_data)
        session.add(trade)
        session.commit()
        logger.info(f"Logged trade: {trade}")
    except SQLAlchemyError as e:
        logger.error(f"Failed to log trade: {e}")
        session.rollback()