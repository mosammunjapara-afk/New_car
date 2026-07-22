"""
main.py — CarYanams Price API (FastAPI server)
===============================================

Poora API server. Isme 2 tarah ke endpoints hain:

CUSTOMER (API key chahiye — ye customers ko bechoge):
  GET  /api/v1/new-car-price   ?brand=&model=&variant=&fuel_type=&state=
  GET  /api/v1/price-history   ?brand=&model=&variant=
  GET  /api/v1/usage           (apni quota dekho)

ADMIN (aapka secret chahiye — sirf aapke liye):
  POST /admin/create-key       naye customer ki key banao
  POST /admin/revoke-key       key band karo
  GET  /admin/keys             saare customers dekho
  POST /admin/trigger-sync     abhi prices update karo
  GET  /admin/cars             saari cars dekho
  GET  /admin/logs             sync logs dekho

Chalane ke liye:
  uvicorn main:app --reload --port 4000
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel

from database import init_db, get_db
import api_keys
from price_sync import run_price_sync

# .env file se settings load karo (agar file ho to)
load_dotenv()

# .env se ya default
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "caryanams_admin_secret_change_this")

app = FastAPI(title="CarYanams Price API", version="1.0")


@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _check_key(x_api_key: str):
    """API key verify + count. Reusable helper."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key (X-API-Key header)")
    result = api_keys.verify_and_count(x_api_key)
    if result == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    if result == "limit":
        raise HTTPException(status_code=429, detail="Monthly API call limit reached")


def require_admin(secret: str):
    if secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")


def calculate_on_road(ex_showroom: int, state: str, conn) -> int:
    """Ex-showroom + RTO tax + insurance = on-road price."""
    row = conn.execute("SELECT * FROM state_tax WHERE state = ?", (state,)).fetchone()
    rto = row["rto_tax_pct"] if row else 0.12          # default 12%
    ins = row["insurance_pct"] if row else 0.04        # default 4%
    return round(ex_showroom * (1 + rto + ins))


# ---------------------------------------------------------------------------
# CUSTOMER endpoints (API key required)
# ---------------------------------------------------------------------------
@app.get("/api/v1/new-car-price")
def get_new_car_price(
    brand: str = Query(...),
    model: str = Query(...),
    variant: str = Query(...),
    fuel_type: str = Query(None),
    state: str = Query(None),
    x_api_key: str = Header(None),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key (X-API-Key header)")

    result = api_keys.verify_and_count(x_api_key)
    if result == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    if result == "limit":
        raise HTTPException(status_code=429, detail="Monthly API call limit reached")

    conn = get_db()
    # 1. exact match (case-insensitive brand/model, exact variant)
    q = "SELECT * FROM cars WHERE LOWER(brand)=LOWER(?) AND LOWER(model)=LOWER(?) AND LOWER(variant)=LOWER(?)"
    params = [brand, model, variant]
    if fuel_type:
        q += " AND LOWER(fuel_type)=LOWER(?)"
        params.append(fuel_type)
    car = conn.execute(q, params).fetchone()

    # 2. na mile to partial match (variant naam ka hissa) — "MX1" -> "MX1 Petrol"
    if car is None:
        q2 = ("SELECT * FROM cars WHERE LOWER(brand)=LOWER(?) AND LOWER(model)=LOWER(?) "
              "AND LOWER(variant) LIKE LOWER(?)")
        params2 = [brand, model, f"%{variant}%"]
        if fuel_type:
            q2 += " AND LOWER(fuel_type)=LOWER(?)"
            params2.append(fuel_type)
        q2 += " ORDER BY ex_showroom_price LIMIT 1"
        car = conn.execute(q2, params2).fetchone()

    if car is None:
        # helpful error: available variants suggest karo
        avail = conn.execute(
            "SELECT variant FROM cars WHERE LOWER(brand)=LOWER(?) AND LOWER(model)=LOWER(?) "
            "ORDER BY ex_showroom_price",
            (brand, model),
        ).fetchall()
        conn.close()
        if avail:
            names = [a["variant"] for a in avail]
            raise HTTPException(
                status_code=404,
                detail=f"Variant '{variant}' not found. Available variants for {brand} {model}: {names}",
            )
        raise HTTPException(status_code=404, detail="Car not found in database (check brand/model spelling)")

    response = {
        "brand": car["brand"],
        "model": car["model"],
        "variant": car["variant"],
        "fuel_type": car["fuel_type"],
        "ex_showroom_price": car["ex_showroom_price"],
        "last_updated": car["last_checked_at"],
    }
    if state:
        response["state"] = state
        response["on_road_price"] = calculate_on_road(car["ex_showroom_price"], state, conn)

    conn.close()
    return response


@app.get("/api/v1/price-history")
def get_price_history(
    brand: str = Query(...),
    model: str = Query(...),
    variant: str = Query(...),
    x_api_key: str = Header(None),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    result = api_keys.verify_and_count(x_api_key)
    if result == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    if result == "limit":
        raise HTTPException(status_code=429, detail="Monthly API call limit reached")

    conn = get_db()
    car = conn.execute(
        "SELECT id FROM cars WHERE brand=? AND model=? AND variant=?",
        (brand, model, variant),
    ).fetchone()
    if car is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Car not found")

    rows = conn.execute(
        "SELECT old_price, new_price, changed_at FROM price_history "
        "WHERE car_id=? ORDER BY changed_at DESC",
        (car["id"],),
    ).fetchall()
    conn.close()
    return {"brand": brand, "model": model, "variant": variant,
            "history": [dict(r) for r in rows]}


@app.get("/api/v1/usage")
def usage(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    u = api_keys.get_usage(x_api_key)
    if u is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return u


# ---------------------------------------------------------------------------
# ADMIN endpoints (admin secret required)
# ---------------------------------------------------------------------------
class CreateKeyBody(BaseModel):
    customer_name: str
    customer_email: str = None
    plan_calls_per_month: int = 1000


class RevokeKeyBody(BaseModel):
    api_key: str


@app.post("/admin/create-key")
def admin_create_key(body: CreateKeyBody, x_admin_secret: str = Header(None)):
    require_admin(x_admin_secret)
    key = api_keys.create_customer_key(
        body.customer_name, body.customer_email, body.plan_calls_per_month
    )
    return {"message": "API key created", "api_key": key,
            "customer_name": body.customer_name,
            "plan_calls_per_month": body.plan_calls_per_month}


@app.post("/admin/revoke-key")
def admin_revoke_key(body: RevokeKeyBody, x_admin_secret: str = Header(None)):
    require_admin(x_admin_secret)
    ok = api_keys.revoke_key(body.api_key)
    if not ok:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"message": "API key revoked"}


@app.get("/admin/keys")
def admin_list_keys(x_admin_secret: str = Header(None)):
    require_admin(x_admin_secret)
    conn = get_db()
    rows = conn.execute(
        "SELECT customer_name, customer_email, plan_calls_per_month, "
        "calls_used_this_month, is_active, created_at FROM api_keys"
    ).fetchall()
    conn.close()
    return {"customers": [dict(r) for r in rows]}


@app.post("/admin/trigger-sync")
def admin_trigger_sync(x_admin_secret: str = Header(None), brand: str = Query(None)):
    require_admin(x_admin_secret)
    result = run_price_sync(only_brand=brand)
    return {"message": "Price sync finished", **result}


@app.get("/admin/cars")
def admin_list_cars(x_admin_secret: str = Header(None)):
    require_admin(x_admin_secret)
    conn = get_db()
    rows = conn.execute(
        "SELECT brand, COUNT(*) as count FROM cars GROUP BY brand ORDER BY count DESC"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) as c FROM cars").fetchone()["c"]
    conn.close()
    return {"total_cars": total, "by_brand": [dict(r) for r in rows]}


@app.get("/admin/logs")
def admin_logs(x_admin_secret: str = Header(None)):
    require_admin(x_admin_secret)
    conn = get_db()
    rows = conn.execute(
        "SELECT brand, status, cars_found, message, ran_at FROM scrape_logs "
        "ORDER BY ran_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return {"logs": [dict(r) for r in rows]}


@app.get("/api/v1/brands")
def list_brands(x_api_key: str = Header(None)):
    """Saare available brands + har brand me kitne cars."""
    _check_key(x_api_key)
    conn = get_db()
    rows = conn.execute(
        "SELECT brand, COUNT(*) as count FROM cars GROUP BY brand ORDER BY brand"
    ).fetchall()
    conn.close()
    return {"brands": [dict(r) for r in rows], "total_brands": len(rows)}


@app.get("/api/v1/models")
def list_models(brand: str = Query(...), x_api_key: str = Header(None)):
    """Ek brand ke saare models + variant count."""
    _check_key(x_api_key)
    conn = get_db()
    rows = conn.execute(
        "SELECT model, COUNT(*) as variants FROM cars WHERE brand=? GROUP BY model ORDER BY model",
        (brand,),
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"brand": brand, "models": [dict(r) for r in rows]}


@app.get("/api/v1/variants")
def list_variants(brand: str = Query(...), model: str = Query(...),
                  x_api_key: str = Header(None)):
    """Ek model ke saare variants + prices (ek call me poori list)."""
    _check_key(x_api_key)
    conn = get_db()
    rows = conn.execute(
        "SELECT variant, fuel_type, ex_showroom_price, last_checked_at "
        "FROM cars WHERE brand=? AND model=? ORDER BY ex_showroom_price",
        (brand, model),
    ).fetchall()
    conn.close()
    if not rows:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"brand": brand, "model": model,
            "variants": [dict(r) for r in rows]}


@app.get("/")
def root():
    return {"status": "CarYanams Price API is running", "docs": "/docs"}