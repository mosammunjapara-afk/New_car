"""
api_keys.py — API key ka poora system
======================================

Ye wahi hai jo Surepass/UBV/DRAM karte hain:
  - naye customer ke liye unique key banao (cyk_...)
  - har request pe key verify karo
  - monthly quota count karo, limit cross ho to block karo
  - 30 din baad quota apne aap 0 (naya cycle)

Customer ko sirf apni key deni hoti hai — bas.
"""

import secrets
from datetime import datetime, timedelta

from database import get_db

THIRTY_DAYS = timedelta(days=30)


def generate_api_key() -> str:
    """Ek naya random API key banata hai. 'cyk_' = CarYanams Key."""
    return "cyk_" + secrets.token_hex(24)


def create_customer_key(customer_name: str, customer_email: str = None,
                        plan_calls_per_month: int = 1000) -> str:
    """Naye customer ke liye key banake DB me save karta hai. (Ye kaam AAP karte ho.)"""
    key = generate_api_key()
    conn = get_db()
    conn.execute(
        """INSERT INTO api_keys (api_key, customer_name, customer_email, plan_calls_per_month)
           VALUES (?, ?, ?, ?)""",
        (key, customer_name, customer_email, plan_calls_per_month),
    )
    conn.commit()
    conn.close()
    return key


def revoke_key(api_key: str) -> bool:
    """Ek key band kar deta hai (customer ne payment nahi ki / cancel kiya)."""
    conn = get_db()
    cur = conn.execute("UPDATE api_keys SET is_active = 0 WHERE api_key = ?", (api_key,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return changed > 0


def verify_and_count(api_key: str):
    """
    Har customer request pe ye chalta hai. Ye 4 cheezein karta hai:
      1. key valid + active hai? nahi -> None (401)
      2. 30 din puraana cycle? -> quota 0 karke naya cycle shuru
      3. quota khatam? -> "limit" (429)
      4. sab theek -> usage +1, customer info return

    Returns:
      dict (customer)  -> sab theek
      "invalid"        -> galat/band key
      "limit"          -> monthly limit cross
    """
    conn = get_db()
    row = conn.execute("SELECT * FROM api_keys WHERE api_key = ?", (api_key,)).fetchone()

    if row is None or row["is_active"] != 1:
        conn.close()
        return "invalid"

    customer = dict(row)

    # --- 30-din auto-reset ---
    try:
        cycle_start = datetime.fromisoformat(customer["cycle_reset_at"])
    except (ValueError, TypeError):
        cycle_start = datetime.now()

    if datetime.now() - cycle_start >= THIRTY_DAYS:
        conn.execute(
            "UPDATE api_keys SET calls_used_this_month = 0, cycle_reset_at = ? WHERE api_key = ?",
            (datetime.now().isoformat(), api_key),
        )
        conn.commit()
        customer["calls_used_this_month"] = 0

    # --- quota check ---
    if customer["calls_used_this_month"] >= customer["plan_calls_per_month"]:
        conn.close()
        return "limit"

    # --- usage +1 ---
    conn.execute(
        "UPDATE api_keys SET calls_used_this_month = calls_used_this_month + 1 WHERE api_key = ?",
        (api_key,),
    )
    conn.commit()
    customer["calls_used_this_month"] += 1
    conn.close()
    return customer


def get_usage(api_key: str):
    """Customer apni bachi hui quota dekh sakta hai."""
    conn = get_db()
    row = conn.execute("SELECT * FROM api_keys WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    if row is None:
        return None
    c = dict(row)
    return {
        "customer_name": c["customer_name"],
        "plan_calls_per_month": c["plan_calls_per_month"],
        "calls_used_this_month": c["calls_used_this_month"],
        "calls_remaining": c["plan_calls_per_month"] - c["calls_used_this_month"],
    }
