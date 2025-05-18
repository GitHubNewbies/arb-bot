from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    exchange = Column(String, nullable=False)
    pair = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="submitted")
