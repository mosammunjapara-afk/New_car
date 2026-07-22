"""
cleanup_history.py — jhoothi (flip-flop) price-change history saaf karo
========================================================================
Pehle duplicate-variant bug ki wajah se price_history me jhoothi entries bhar
gayi thi (same variant A->B->A baar-baar). Ab dedup fix ho gaya hai, toh ye
purani galat history ek baar clear kar dete hain — fresh start.

Ye sirf price_history table khaali karta hai. cars table (current prices)
ko haath nahi lagata — wo safe hai.

CHALAO:
    python cleanup_history.py
"""

import sqlite3

DB = "caryanams.db"

conn = sqlite3.connect(DB)
before = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
cars = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]

print(f"Abhi: {cars} cars, {before} price-history entries")
print("price_history clear kar rahe hain (cars safe rahenge)...")

conn.execute("DELETE FROM price_history")
# id counter bhi reset (optional, saaf dikhne ke liye)
try:
    conn.execute("DELETE FROM sqlite_sequence WHERE name='price_history'")
except Exception:
    pass
conn.commit()

after = conn.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
cars_after = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
conn.close()

print(f"Ho gaya: {after} history entries (tha {before}), {cars_after} cars safe hain.")
print("\nAb agli baar 'python price_sync.py' chalao — sirf ASLI price changes")
print("hi history me aayenge, flip-flop nahi.")