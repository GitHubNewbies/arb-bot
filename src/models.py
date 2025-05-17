from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Text

Base = declarative_base()

class TradeHistory(Base):
    __tablename__ = 'trade_history'

    id = Column(Integer, primary_key=True, index=True)
    exchange = Column(String, nullable=False)
    pair = Column(String, nullable=False)
    side = Column(String, nullable=False)
    quantity = Column(Numeric, nullable=False)
    price = Column(Numeric, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(Text, nullable=True)  # nullable for successful trades without errors
