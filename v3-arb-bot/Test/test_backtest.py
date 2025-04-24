import pandas as pd
from src.backtest import simulate

def test_backtest_synthetic(monkeypatch):
    class FakeEx:
        def fetch_ohlcv(self, *a, **k):
            return [[0,100,110,90,105,1]]
    import ccxt
    monkeypatch.setattr(ccxt, "binance", lambda **kwargs: FakeEx())
    simulate("FAKE/USDC", 0, 60000, 50, 0.01)
