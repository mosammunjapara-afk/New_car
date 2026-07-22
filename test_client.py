"""
test_client.py — API ko test karne ke liye (Python)
====================================================

Ye wahi tarika hai jaise CUSTOMER API use karega — sirf ek API key se.

Chalane se pehle:
  1. Server chalu karo (doosre terminal me):
        uvicorn main:app --port 4000
  2. Phir ye chalao:
        python test_client.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "http://localhost:4000"
# .env se wahi secret padhta hai jo server padhta hai — dono hamesha match rahenge
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "caryanams_admin_secret_change_this")


def create_key(name, calls=5000):
    r = requests.post(f"{API_BASE}/admin/create-key",
                      headers={"X-Admin-Secret": ADMIN_SECRET},
                      json={"customer_name": name, "plan_calls_per_month": calls})
    r.raise_for_status()
    return r.json()["api_key"]


def get_price(key, brand, model, variant, fuel_type=None, state=None):
    params = {"brand": brand, "model": model, "variant": variant}
    if fuel_type:
        params["fuel_type"] = fuel_type
    if state:
        params["state"] = state
    r = requests.get(f"{API_BASE}/api/v1/new-car-price",
                     headers={"X-API-Key": key}, params=params)
    return r.status_code, r.json()


if __name__ == "__main__":
    print("STEP 1 — prices sync karo (admin)")
    r = requests.post(f"{API_BASE}/admin/trigger-sync",
                      headers={"X-Admin-Secret": ADMIN_SECRET})
    print(" ", r.json())

    print("\nSTEP 2 — naye customer ki API key banao")
    key = create_key("Test Customer")
    print("  Key:", key)

    print("\nSTEP 3 — customer key se price maange")
    status, data = get_price(key, "Maruti Suzuki", "swift", "ZXi MT",
                             fuel_type="Petrol", state="Gujarat")
    print("  HTTP", status, "->", data)

    print("\nSTEP 4 — quota check")
    r = requests.get(f"{API_BASE}/api/v1/usage", headers={"X-API-Key": key})
    print(" ", r.json())

    print("\nSTEP 5 — galat key (fail hona chahiye)")
    status, data = get_price("cyk_galat123", "Maruti Suzuki", "swift", "ZXi MT")
    print("  HTTP", status, "->", data)