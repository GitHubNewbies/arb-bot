import os, time, sqlite3, pathlib
import streamlit as st
import pandas as pd
from dotenv import load_dotenv, set_key
from src.config import SQLITE_DB_PATH

# Bootstrap local data folder
pathlib.Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

load_dotenv(); ENV=".env"
st.sidebar.header("⚙️ Settings")

pairs = st.sidebar.text_input("Pairs (csv)", os.getenv("PAIR"))
thr   = st.sidebar.slider("Threshold %", 0.1, 5.0, float(os.getenv("SPREAD_THRESHOLD"))*100)/100
notnl = st.sidebar.number_input("Notional $", 0.0, 1000.0, float(os.getenv("DESIRED_NOTIONAL_USD")))

if st.sidebar.button("Save"):
    set_key(ENV, "PAIR", pairs)
    set_key(ENV, "SPREAD_THRESHOLD", str(thr))
    set_key(ENV, "DESIRED_NOTIONAL_USD", str(notnl))
    st.success("✅ Saved. Restart engine.")

mins = st.sidebar.slider("Last N min", 1, 1440, 60)

conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
ph   = ",".join("?"*len(pairs.split(",")))
sql  = f"""
SELECT ts,pair,direction,bid,ask,spread,profit
FROM log
WHERE ts >= ? AND pair IN ({ph})
ORDER BY ts
"""
params = [time.time()-mins*60] + pairs.split(",")
df = pd.read_sql(sql, conn, params=params)
df["dt"] = pd.to_datetime(df["ts"], unit="s")

st.title("🚀 V3 Arbitrage Bot Dashboard")
st.markdown(f"Showing last **{mins} minutes** for `{pairs}`")

st.subheader("📜 Log")
st.dataframe(df[["dt","pair","direction","bid","ask","spread","profit"]], use_container_width=True)

st.subheader("📈 Cumulative Profit")
if not df.empty:
    trades = df[df["direction"]!="scan"].copy()
    trades["cum"] = trades.groupby("pair")["profit"].cumsum()
    st.line_chart(trades.pivot(index="dt", columns="pair", values="cum").fillna(method="ffill"))
else:
    st.info("No trades or scans in that window.")

conn.close()
