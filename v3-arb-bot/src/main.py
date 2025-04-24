import asyncio, logging
from .init_db import initialize_database
from .notify    import send_startup_alert
from .engine    import arbitrage, binance, bybit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

async def run_loop():
    while True:
        try:
            await arbitrage()
        except Exception as e:
            logging.error("Error in arb loop: %s", e)
        await asyncio.sleep(5)

if __name__ == "__main__":
    initialize_database()
    send_startup_alert()
    try:
        asyncio.run(run_loop())
    finally:
        asyncio.run(binance.close())
        asyncio.run(bybit.close())
