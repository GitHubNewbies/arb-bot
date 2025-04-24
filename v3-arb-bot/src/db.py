import time, pathlib
from urllib.parse import urlparse
from .config import DATABASE_URL, SQLITE_DB_PATH

if DATABASE_URL.startswith("sqlite"):
    import sqlite3
    pathlib.Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
else:
    import psycopg2
    url = urlparse(DATABASE_URL)
    _conn = psycopg2.connect(
        dbname=url.path.lstrip("/"),
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
    )

_cur = _conn.cursor()

def log_event(pair, direction, bid, ask, spread, profit):
    _cur.execute(
        "INSERT INTO log(ts,pair,direction,bid,ask,spread,profit) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (time.time(), pair, direction, bid, ask, spread, profit),
    )
    _conn.commit()
