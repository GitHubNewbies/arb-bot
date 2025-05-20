import logging
from decimal import Decimal
from typing import List, Optional

from src.exchanges.binance import BinanceAdapter
from src.exchanges.bybit import BybitAdapter
from src.exchanges.discovery import get_common_pairs
from src.database import get_db_session
from src.models import OpportunityLog

logger = logging.getLogger("arb-bot")


ARBITRAGE_THRESHOLD = Decimal("0.5")  # percent


def calculate_spread(p1: Decimal, p2: Decimal) -> Decimal:
    """
    Returns the percentage spread between two prices.
    """
    return abs((p1 - p2) / ((p1 + p2) / 2)) * 100


def scan_market(pairs: list[str], session, binance, bybit) -> None:
    """
    Scans common tradable pairs and checks for arbitrage opportunities.
    Logs each opportunity to the database for future AI/ML use.
    """
    # Ensure Bybit symbols are fetched before any price or quantity calls
    bybit.get_tradable_pairs()
    logger.info("📄 Loaded Bybit symbol map for linear contracts.")

    if not pairs:
        logger.warning("⚠️ No common trading pairs found — exiting.")
        return

    for pair in pairs:
        try:
            base, _ = pair.split("/")
        except ValueError:
            logger.error(f"❌ Invalid pair format: {pair}")
            continue

        logger.info(f"🔍 Scanning {pair}")

        # --- Binance fetch ---
        try:
            binance_price = binance.fetch_price(pair)
            if not binance_price:
                logger.warning(f"⚠️ No price data for {pair} on Binance.")
            else:
                logger.debug(f"🔢 Binance price for {pair}: {binance_price}")

            logger.info(f"📊 Fetching balance for USDC to calculate quantity for {pair} ({binance_price})")
            binance_balance = binance.get_balance("USDC")
            binance_qty = (
                binance.calculate_quantity(
                    pair,
                    binance_price,
                    "BUY",
                    binance_balance
                ) if binance_price is not None else None
            )
            logger.debug(f"📦 Binance quantity for {pair}: {binance_qty}")
        except Exception as e:
            logger.error(f"❌ Binance error for {pair}: {e}")
            binance_price = binance_qty = None

        if not binance_qty:
            logger.warning(f"⚠️ Skipping {pair} on binance: quantity is zero.")

        # --- Bybit fetch ---
        try:
            bybit_price = bybit.fetch_price(pair)
            if not bybit_price:
                logger.warning(f"⚠️ No price data for {pair} on Bybit.")
            else:
                logger.debug(f"🔢 Bybit price for {pair}: {bybit_price}")

            logger.info(f"📊 Fetching balance for USDC to calculate quantity for {pair} ({bybit_price})")
            bybit_balance = bybit.get_balance("USDC")
            try:
                bybit_qty_sell = bybit.calculate_quantity(pair, bybit_price, "SELL", bybit_balance)
                logger.debug(f"📦 Bybit SELL quantity for {pair}: {bybit_qty_sell}")
            except Exception as e:
                logger.error(f"❌ Bybit SELL quantity error for {pair}: {e}")
                bybit_qty_sell = None

            try:
                bybit_qty_buy = bybit.calculate_quantity(pair, bybit_price, "BUY", bybit_balance)
                logger.debug(f"📦 Bybit BUY quantity for {pair}: {bybit_qty_buy}")
            except Exception as e:
                logger.error(f"❌ Bybit BUY quantity error for {pair}: {e}")
                bybit_qty_buy = None

        except Exception as e:
            logger.error(f"❌ Bybit error for {pair}: {e}")
            bybit_price = bybit_qty_sell = bybit_qty_buy = None

        # Evaluate both arbitrage directions
        if isinstance(binance_price, Decimal) and isinstance(bybit_price, Decimal):
            spread_1 = calculate_spread(binance_price, bybit_price)
            spread_2 = calculate_spread(bybit_price, binance_price)

            # Direction A: Buy Binance, Sell Bybit
            if spread_1 >= ARBITRAGE_THRESHOLD and binance_qty and bybit_qty_sell:
                qty = min(binance_qty, bybit_qty_sell)
                logger.info(
                    f"🟢 Arbitrage Opportunity on {pair}: Buy on Binance @ {binance_price}, "
                    f"Sell on Bybit @ {bybit_price} | Spread: {spread_1:.2f}% | Qty: {qty}"
                )
                try:
                    log = OpportunityLog(
                        pair=pair,
                        exchange_buy="Binance",
                        exchange_sell="Bybit",
                        price_buy=binance_price,
                        price_sell=bybit_price,
                        spread=spread_1,
                        quantity=qty
                    )
                    session.add(log)
                    session.commit()
                except Exception as e:
                    if session.is_active:
                        session.rollback()
                    logger.error(f"❌ DB logging failed (Binance→Bybit) for {pair}: {e}")

            # Direction B: Buy Bybit, Sell Binance
            if spread_2 >= ARBITRAGE_THRESHOLD and bybit_qty_buy and binance_qty:
                qty = min(bybit_qty_buy, binance_qty)
                logger.info(
                    f"🟢 Arbitrage Opportunity on {pair}: Buy on Bybit @ {bybit_price}, "
                    f"Sell on Binance @ {binance_price} | Spread: {spread_2:.2f}% | Qty: {qty}"
                )
                try:
                    log = OpportunityLog(
                        pair=pair,
                        exchange_buy="Bybit",
                        exchange_sell="Binance",
                        price_buy=bybit_price,
                        price_sell=binance_price,
                        spread=spread_2,
                        quantity=qty
                    )
                    session.add(log)
                    session.commit()
                except Exception as e:
                    if session.is_active:
                        session.rollback()
                    logger.error(f"❌ DB logging failed (Bybit→Binance) for {pair}: {e}")
            else:
                logger.debug(f"Spread too low on {pair}: {spread_1:.2f}% / {spread_2:.2f}%")