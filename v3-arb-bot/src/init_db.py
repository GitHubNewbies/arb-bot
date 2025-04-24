import os, pathlib
import psycopg2
from urllib.parse import urlparse
from .config import DATABASE_URL, SQLITE_DB_PATH

# Ensure local dir for SQLite if used
if DATABASE_URL.startswith("sqlite"):
    pathlib.Path(SQLITE_DB_PATH).parent.mkdir(parents=True, exist_ok=True)

def initialize_database():
    if DATABASE_URL.startswith("sqlite"):
        import sqlite3
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    else:
        url = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            dbname=url.path.lstrip("/"),
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port,
        )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS log (
            ts        DOUBLE PRECISION,
            pair      TEXT,
            direction TEXT,
            bid       DOUBLE PRECISION,
            ask       DOUBLE PRECISION,
            spread    DOUBLE PRECISION,
            profit    DOUBLE PRECISION
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    initialize_database()
    print("✅ Database schema initialized.")
