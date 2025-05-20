from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum
from datetime import datetime

Base = declarative_base()

class TradeLog(Base):
    """
    Represents a trade record with details about the executed trade,
    including pair, exchange, side (BUY/SELL), quantity, price, and status.
    """

    __tablename__ = "trade_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pair = Column(String, index=True, nullable=False)
    exchange = Column(String, index=True, nullable=False)
    side = Column(Enum("BUY", "SELL", name="trade_side"), nullable=False)
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)
    price = Column(Numeric(precision=18, scale=8), nullable=False)
    status = Column(String, nullable=False)
    notes = Column(String, nullable=True)

    def __repr__(self):
        return (f"<TradeLog(id={self.id}, pair='{self.pair}', exchange='{self.exchange}', side='{self.side}', "
                f"quantity={self.quantity}, price={self.price}, status='{self.status}', timestamp={self.timestamp})>")


class OpportunityLog(Base):
    """
    Represents an arbitrage opportunity detected between two exchanges,
    recording the trading pair, buy/sell exchanges, prices, spread, and quantity.
    """

    __tablename__ = "opportunity_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    pair = Column(String, nullable=False)
    exchange_buy = Column(String, nullable=False)
    exchange_sell = Column(String, nullable=False)
    price_buy = Column(Numeric(precision=18, scale=8), nullable=False)
    price_sell = Column(Numeric(precision=18, scale=8), nullable=False)
    spread = Column(Numeric(precision=18, scale=4), nullable=False)
    quantity = Column(Numeric(precision=18, scale=8), nullable=False)

    def __repr__(self):
        return (f"<OpportunityLog(id={self.id}, pair='{self.pair}', exchange_buy='{self.exchange_buy}', "
                f"exchange_sell='{self.exchange_sell}', price_buy={self.price_buy}, price_sell={self.price_sell}, "
                f"spread={self.spread}, quantity={self.quantity}, timestamp={self.timestamp})>")