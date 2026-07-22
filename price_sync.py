"""
price_sync.py — Automatic price update + change detection
==========================================================

Ye system ka dil hai. Har scraper se nayi prices leta hai, aur:
  - agar price BADLI hai -> purani price history me save, nayi price update
  - agar price wahi hai   -> kuch nahi

Yahi wo "automatic price change" hai jo aap chahti thi. Jab showroom pe
discount aata hai aur manufacturer website pe price girti hai, ye use pakad
leta hai aur aapke DB me update kar deta hai.

Scrapers alag file me hain (scrapers/ folder). Har brand ka apna scraper.
"""

from database import get_db
from scrapers import ACTIVE_SCRAPERS


def upsert_car_price(conn, brand, model, variant, fuel_type, new_price):
    """
    Ek car ka price DB me daalta/update karta hai + change detect karta hai.
    Returns: "new" (nayi car), "changed" (price badla), ya "same" (koi change nahi)
    """
    row = conn.execute(
        """SELECT * FROM cars
           WHERE brand=? AND model=? AND variant=? AND IFNULL(fuel_type,'')=IFNULL(?,'')""",
        (brand, model, variant, fuel_type),
    ).fetchone()

    if row is None:
        # bilkul nayi car
        conn.execute(
            """INSERT INTO cars (brand, model, variant, fuel_type, ex_showroom_price)
               VALUES (?, ?, ?, ?, ?)""",
            (brand, model, variant, fuel_type, new_price),
        )
        return "new"

    old_price = row["ex_showroom_price"]
    if old_price != new_price:
        # PRICE CHANGE DETECT HUA — history save karo, phir update
        conn.execute(
            "INSERT INTO price_history (car_id, old_price, new_price) VALUES (?, ?, ?)",
            (row["id"], old_price, new_price),
        )
        conn.execute(
            "UPDATE cars SET ex_showroom_price=?, last_checked_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_price, row["id"]),
        )
        print(f"    PRICE CHANGED: {brand} {model} {variant}: "
              f"Rs {old_price} -> Rs {new_price}")
        return "changed"
    else:
        # price wahi hai, sirf "last checked" time update
        conn.execute(
            "UPDATE cars SET last_checked_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],)
        )
        return "same"


def run_price_sync(only_brand: str = None):
    """
    Saare active scrapers chalata hai aur DB update karta hai.
    only_brand: agar diya, sirf usi brand ka scraper chalega (testing ke liye).
    """
    conn = get_db()
    total_new = total_changed = total_same = 0

    for brand, scraper_fn in ACTIVE_SCRAPERS.items():
        if only_brand and brand != only_brand:
            continue

        print(f"[sync] {brand} scraping...")
        try:
            cars = scraper_fn()  # har scraper list of dicts deta hai
        except Exception as e:
            print(f"[sync] {brand} FAILED: {e}")
            conn.execute(
                "INSERT INTO scrape_logs (brand, status, cars_found, message) VALUES (?,?,?,?)",
                (brand, "error", 0, str(e)),
            )
            conn.commit()
            continue

        n_new = n_changed = n_same = 0
        for car in cars:
            result = upsert_car_price(
                conn, brand, car["model"], car["variant"],
                car.get("fuel_type"), car["ex_showroom_price"],
            )
            if result == "new":
                n_new += 1
            elif result == "changed":
                n_changed += 1
            else:
                n_same += 1

        conn.execute(
            "INSERT INTO scrape_logs (brand, status, cars_found, message) VALUES (?,?,?,?)",
            (brand, "ok", len(cars),
             f"{n_new} new, {n_changed} changed, {n_same} same"),
        )
        conn.commit()
        print(f"[sync] {brand}: {len(cars)} cars ({n_new} new, {n_changed} changed, {n_same} same)")
        total_new += n_new
        total_changed += n_changed
        total_same += n_same

    conn.close()
    print(f"[sync] DONE — {total_new} new, {total_changed} changed, {total_same} same")
    return {"new": total_new, "changed": total_changed, "same": total_same}


if __name__ == "__main__":
    run_price_sync()