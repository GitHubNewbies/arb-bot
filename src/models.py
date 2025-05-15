from sqlalchemy import Column, String, Float, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class Opportunity(Base):
    __tablename__ = 'opportunities'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    pair = Column(String)
    buy_exchange = Column(String)
    sell_exchange = Column(String)
    buy_price = Column(Numeric)
    sell_price = Column(Numeric)
    spread_pct = Column(Numeric)
    notional = Column(Numeric)
    reason_skipped = Column(String, nullable=True)
    meta = Column(JSONB, nullable=True)

class ExecutedTrade(Base):
    __tablename__ = 'executed_trades'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey('opportunities.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    exchange = Column(String)
    side = Column(String)
    amount = Column(Numeric)
    price = Column(Numeric)
    fee = Column(Numeric)
    status = Column(String)
    pnl = Column(Numeric)
    meta = Column(JSONB)

class BotError(Base):
    __tablename__ = 'bot_errors'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    module = Column(String)
    message = Column(Text)
    stacktrace = Column(Text, nullable=True)
    context = Column(JSONB, nullable=True)
