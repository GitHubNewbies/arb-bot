# src/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from src.models import TradeLog  # Ensure all models are imported

import os

Base = declarative_base()

# Example: postgresql://user:password@host/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trades.db")

# Set up the database engine and session factory
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_db_session() -> Session:
    """Returns a new SQLAlchemy session."""
    return SessionLocal()


def create_all_tables():
    """Ensures all DB tables are created."""
    Base.metadata.create_all(bind=engine)
