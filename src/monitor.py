

import logging
from database import get_session
from models import TradePosition

logger = logging.getLogger("arb-bot")

def monitor_open_positions():
    logger.info("🔍 Monitoring open positions...")
    session = get_session()
    try:
        positions = session.query(TradePosition).filter_by(is_open=True).all()
        for pos in positions:
            logger.debug(f"📈 Open Position: {pos.exchange} {pos.pair} | Entry: {pos.entry_price} | Side: {pos.side}")

            # Example: check if unrealized PnL has crossed threshold
            if pos.unrealized_profit_pct is not None:
                if pos.unrealized_profit_pct >= pos.take_profit_pct:
                    logger.info(f"💰 Trigger take-profit for {pos.exchange} {pos.pair}")
                    # queue close logic
                elif pos.unrealized_profit_pct <= -pos.stop_loss_pct:
                    logger.warning(f"🔻 Trigger stop-loss for {pos.exchange} {pos.pair}")
                    # queue close logic
    except Exception as e:
        logger.error(f"❌ Error during position monitoring: {e}")
    finally:
        session.close()