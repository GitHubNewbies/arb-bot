import os
import logging
from decimal import Decimal
from datetime import datetime

import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Numeric, TIMESTAMP, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLAlchemy setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("❌ DATABASE_URL environment variable not set.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Table model
class TradeHistory(Base):
    __tablename__ = 'trade_history'

    id = Column(Integer, primary_key=True, index=True)
    exchange = Column(String, nullable=False)
    pair = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Numeric(20, 10), nullable=False)
    price = Column(Numeric(20, 10), nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(Text)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)


# Create table if not exists
def ensure_tables_exist():
    try:
        Base.metadata.create_all(bind=engine)
        logging.info("✅ Ensured all tables exist.")
    except Exception as e:
        logging.exception("❌ Failed to create tables.")
        raise


# Get a new session
def get_session():
    return SessionLocal()


# Insert trade record
def save_trade_history(session, exchange, pair, side, quantity, price, status, error_message=None):
    try:
        trade = TradeHistory(
            exchange=exchange,
            pair=pair,
            side=side,
            quantity=Decimal(quantity),
            price=Decimal(price),
            status=status,
            error_message=error_message
        )
        session.add(trade)
        session.commit()
        logging.info(f"✅ Logged trade to database: {exchange} {pair} {side} @ {price}")
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to save trade history.")
        raise