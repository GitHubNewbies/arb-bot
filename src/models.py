from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum
from datetime import datetime

Base = declarative_base()

class TradeLog(Base):
    __tablename__ = "trade_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pair = Column(String, index=True)
    exchange = Column(String, index=True)
    side = Column(Enum("BUY", "SELL", name="trade_side"))
    quantity = Column(Numeric(precision=18, scale=8))
    price = Column(Numeric(precision=18, scale=8))
    status = Column(String)
    notes = Column(String, nullable=True)
