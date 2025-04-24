import argparse, ccxt, pandas as pd
from .engine import get_valid_amount

def load_ohlcv(exchange, pair, timeframe, since, limit):
    data = exchange.fetch_ohlcv(pair, timeframe=timeframe, since=since, limit=limit)
    return pd.DataFrame(data, columns=["ts","open","high","low","close","vol"])

def simulate(pair, start_ts, end_ts, notional, threshold):
    ex = ccxt.binance()
    df = load_ohlcv(ex, pair, "1m", start_ts, (end_ts - start_ts)//60000)
    profit = 0.0
    for _, row in df.iterrows():
        bid, ask = row["low"], row["high"]
        spread = (ask - bid)/bid
        if spread >= threshold:
            amt = get_valid_amount(ex, pair, notional)
            profit += (ask - bid)*amt
    print(f"Backtest {pair}: ≈${profit:.2f}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pair", required=True)
    p.add_argument("--from", dest="start", type=int, required=True)
    p.add_argument("--to",   dest="end",   type=int, required=True)
    p.add_argument("--notional", type=float, default=50.0)
    p.add_argument("--threshold", type=float, default=0.004)
    args = p.parse_args()
    simulate(args.pair, args.start, args.end, args.notional, args.threshold)
