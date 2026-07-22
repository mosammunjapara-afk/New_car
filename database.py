"""
database.py — SQLite database setup (Python version)
=====================================================

Ye poore system ka data rakhta hai:
  - cars           : har car variant aur uska current price
  - price_history  : jab bhi price change ho, purani->nayi price yahan save hoti hai
  - state_tax      : har state ka RTO tax % (on-road price ke liye)
  - api_keys       : customers ki API keys + unki usage/quota

SQLite use kiya hai — matlab ek hi file (caryanams.db), koi alag database
server install nahi karna. Baad me MySQL/Postgres pe move karna ho to sirf
ye file badalni padegi.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "caryanams.db"


def get_db():
    """Ek naya database connection deta hai. Har request apna connection use karti hai."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # taaki result dict jaisa mile (column names se access)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Saari tables banata hai agar pehle se na hon. Server start pe ek baar chalta hai."""
    conn = get_db()
    cur = conn.cursor()

    # --- cars: har variant ek row ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            brand             TEXT    NOT NULL,
            model             TEXT    NOT NULL,
            variant           TEXT    NOT NULL,
            fuel_type         TEXT,
            ex_showroom_price INTEGER NOT NULL,
            last_checked_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(brand, model, variant, fuel_type)
        )
    """)

    # --- price_history: har price change ka record ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id      INTEGER NOT NULL,
            old_price   INTEGER,
            new_price   INTEGER NOT NULL,
            changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )
    """)

    # --- state_tax: on-road price nikalne ke liye ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS state_tax (
            state       TEXT PRIMARY KEY,
            rto_tax_pct REAL NOT NULL,   -- e.g. 0.12 = 12%
            insurance_pct REAL NOT NULL DEFAULT 0.04
        )
    """)

    # --- api_keys: customers ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key               TEXT UNIQUE NOT NULL,
            customer_name         TEXT NOT NULL,
            customer_email        TEXT,
            plan_calls_per_month  INTEGER NOT NULL DEFAULT 1000,
            calls_used_this_month INTEGER NOT NULL DEFAULT 0,
            cycle_reset_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active             INTEGER NOT NULL DEFAULT 1,
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- scrape_logs: har sync ka record (debugging ke liye) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scrape_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            brand       TEXT,
            status      TEXT,
            cars_found  INTEGER,
            message     TEXT,
            ran_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Kuch default state tax rates daal do (approximate — apne hisaab se update karna)
    default_states = [
        ("Gujarat", 0.12, 0.04),
        ("Maharashtra", 0.13, 0.04),
        ("Delhi", 0.10, 0.04),
        ("Karnataka", 0.15, 0.04),
        ("Tamil Nadu", 0.13, 0.04),
        ("Uttar Pradesh", 0.10, 0.04),
        ("Rajasthan", 0.10, 0.04),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO state_tax (state, rto_tax_pct, insurance_pct) VALUES (?, ?, ?)",
        default_states,
    )

    conn.commit()
    conn.close()
    print("[database] tables ready")


if __name__ == "__main__":
    init_db()
