"""
scrapers/brands/jeep.py — Jeep India scraper (DIRECT one3d API)
===============================================================

Jeep ka official API (Citroen jaisa one3d platform; visualizer page pe fire):
  https://prod-jeep-api.one3d.in/api/v1/variants/all

Response: response.model_name + response.variants[] with clean fields:
  variant_name       -> "Longitude Plus"
  price              -> exact ex-showroom
  fuel_type          -> "Diesel" / "Petrol"
  transmission_type  -> "Manual" / "Automatic"
  drive              -> "4x2" / "4x4"

Same variant_name MT/AT dono aate hain — transmission+drive naam me add karke
unique karte hain.
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

VISUALIZER_PAGES = [
    ("Compass", "https://www.jeep-india.com/new-compass/visualizer.html"),
    ("Meridian", "https://www.jeep-india.com/new-jeep-meridian/visualizer.html"),
    ("Wrangler", "https://www.jeep-india.com/wrangler-jl/visualizer.html"),
    ("Grand Cherokee", "https://www.jeep-india.com/new-grand-cherokee/visualizer.html"),
]

MODEL_NAME_FIX = {
    "NEW COMPASS": "Compass",
    "MERIDIAN": "Meridian",
    "Wrangler": "Wrangler",
    "GRAND CHEROKEE": "Grand Cherokee",
    "NEW GRAND CHEROKEE": "Grand Cherokee",
}


def _norm_trans(t):
    t = (t or "").lower()
    if "auto" in t:
        return "AT"
    if "manual" in t:
        return "MT"
    return ""


def _clean_variant(v):
    """variant_name + transmission + drive taaki unique + informative."""
    name = (v.get("variant_name") or "").strip()
    trans = _norm_trans(v.get("transmission_type"))
    drive = (v.get("drive") or "").strip()  # 4x2 / 4x4
    parts = [name]
    # transmission agar naam me nahi
    if trans and trans.lower() not in name.lower() and "at" not in name.lower().split() and "mt" not in name.lower().split():
        parts.append(trans)
    # drive agar naam me nahi aur 4x4 hai (4x2 default chhod sakte, par rakhte hain distinguish ke liye)
    if drive and drive.lower() not in name.lower():
        parts.append(drive)
    result = " ".join(parts)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def _parse_model(resp_json, fallback_model):
    out = []
    seen = set()
    r = resp_json.get("response", resp_json) if isinstance(resp_json, dict) else {}
    raw = r.get("model_name", fallback_model)
    model_name = MODEL_NAME_FIX.get(raw, raw.title() if raw.isupper() else raw)
    for v in r.get("variants", []):
        if not isinstance(v, dict):
            continue
        price = v.get("price")
        if not price:
            continue
        try:
            price = int(price)
        except Exception:
            continue
        if not (500000 < price < 30000000):
            continue
        variant = _clean_variant(v)
        fuel = (v.get("fuel_type") or "Petrol").strip().title()
        if fuel not in ("Petrol", "Diesel", "Electric", "Cng", "Hybrid"):
            fuel = "Petrol"
        if fuel == "Cng":
            fuel = "CNG"
        key = (model_name, variant, price)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "model": model_name,
            "variant": variant,
            "fuel_type": fuel,
            "ex_showroom_price": price,
        })
    return out


def scrape_jeep():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        captured = {}
        current = {"model": None}
        def on_response(resp):
            if "one3d.in/api/v1/variants/all" in resp.url:
                try:
                    captured[current["model"]] = resp.text()
                except Exception:
                    pass
        page.on("response", on_response)

        for model, url in VISUALIZER_PAGES:
            current["model"] = model
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=50000)
                page.wait_for_timeout(6000)
                for _ in range(6):
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(500)
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"  [Jeep] {model} page fail: {str(e)[:40]}")

        for model, body in captured.items():
            try:
                data = _json.loads(body)
                rows = _parse_model(data, model)
                if rows:
                    print(f"  [Jeep] {rows[0]['model']}: {len(rows)} variant(s)")
                all_results.extend(rows)
            except Exception as e:
                print(f"  [Jeep] {model} parse fail: {str(e)[:40]}")

        if not all_results:
            print("  [Jeep] koi variant nahi mila")
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_jeep()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)