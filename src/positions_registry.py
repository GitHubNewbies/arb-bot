

import logging
from decimal import Decimal
from typing import Dict, Optional
from uuid import uuid4
from datetime import datetime

from .database import get_db_connection

logger = logging.getLogger("arb-bot")

class Position:
    def __init__(self, symbol: str, exchange: str, side: str, quantity: Decimal, entry_price: Decimal):
        self.id = str(uuid4())
        self.symbol = symbol
        self.exchange = exchange
        self.side = side  # 'BUY' or 'SELL'
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_time = datetime.utcnow()
        self.exit_price: Optional[Decimal] = None
        self.exit_time: Optional[datetime] = None
        self.status = "OPEN"

    def close(self, exit_price: Decimal):
        self.exit_price = exit_price
        self.exit_time = datetime.utcnow()
        self.status = "CLOSED"

    def to_dict(self):
        return {
            "id": self.id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "side": self.side,
            "quantity": str(self.quantity),
            "entry_price": str(self.entry_price),
            "entry_time": self.entry_time.isoformat(),
            "exit_price": str(self.exit_price) if self.exit_price else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "status": self.status
        }

class PositionRegistry:
    def __init__(self):
        self.positions: Dict[str, Position] = {}

    def open_position(self, symbol: str, exchange: str, side: str, quantity: Decimal, price: Decimal) -> str:
        pos = Position(symbol, exchange, side, quantity, price)
        self.positions[pos.id] = pos
        logger.info(f"📈 Opened {side} position on {symbol} at {price} (qty: {quantity}) via {exchange}")
        self._persist_position(pos)
        return pos.id

    def close_position(self, position_id: str, exit_price: Decimal):
        pos = self.positions.get(position_id)
        if not pos:
            logger.warning(f"⚠️ Tried to close unknown position ID: {position_id}")
            return
        pos.close(exit_price)
        logger.info(f"📉 Closed {pos.side} position on {pos.symbol} at {exit_price} (qty: {pos.quantity}) via {pos.exchange}")
        self._persist_position(pos)

    def _persist_position(self, pos: Position):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO positions (
                id, symbol, exchange, side, quantity, entry_price, entry_time,
                exit_price, exit_time, status
            ) VALUES (
                %(id)s, %(symbol)s, %(exchange)s, %(side)s, %(quantity)s, %(entry_price)s, %(entry_time)s,
                %(exit_price)s, %(exit_time)s, %(status)s
            )
            ON CONFLICT (id) DO UPDATE SET
                exit_price = EXCLUDED.exit_price,
                exit_time = EXCLUDED.exit_time,
                status = EXCLUDED.status;
        """, pos.to_dict())
        conn.commit()
        cur.close()
        conn.close()