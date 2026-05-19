import logging
import sys
import sqlite3
from datetime import datetime

# Setup Logging
logger = logging.getLogger("E11_Core")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Database Storage for Journal & Performance
DB_PATH = "e11_sniper.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            bias TEXT,
            price REAL,
            sl REAL,
            tp REAL
        )
    ''')
    conn.commit()
    conn.close()

def log_signal(ticker, bias, price, sl, tp):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO signals (timestamp, ticker, bias, price, sl, tp) VALUES (?, ?, ?, ?, ?, ?)",
                       (datetime.now().isoformat(), ticker, bias, price, sl, tp))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Database insertion error: {e}")

init_db()
