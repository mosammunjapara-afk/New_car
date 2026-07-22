"""
scrapers/brands/hyundai.py — Hyundai scraper (clean JSON API)
==============================================================

Hyundai ke 2 API:
  1. getModels — saare models (id, code, description, exPrice)
  2. getPriceByModelAndCity?cityId=<id>&modelId=<id> — us model ke saare variants
     (Petrol + Diesel + Turbo, sab ek saath!)

Dono seedha khulte hain (Tata jaisa session jhamela nahi). Bas cityId chahiye
(Mumbai=1330 use karte hain — Maharashtra prices standard hain).

Data: variant, fuelType, engine, transmission, edition, price
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

API_BASE = "https://api.hyundai.co.in/service/price"
CITY_ID = 1330  # Mumbai (Maharashtra) — ex-showroom prices

# EV models jinke variant API me BaaS/alag pricing ho sakti hai — abhi normal try karenge
# Taxi/fleet "PRIME" ko skip karte hain (institutional)
SKIP_MODELS = {"PRIME"}


def _detect_fuel(v):
    f = (v.get("fuelType") or "").lower()
    if "diesel" in f:
        return "Diesel"
    if "cng" in f:
        return "CNG"
    if "electric" in f or "ev" in f:
        return "Electric"
    return "Petrol"


def _clean_variant(v):
    variant = (v.get("variant") or "").strip()
    engine = (v.get("engine") or "").strip()
    trans = (v.get("transmission") or "").strip()
    edition = (v.get("edition") or "").strip()
    # engine bhi naam me daalte hain — Verna/Venue me same trim (jaise "HX 8 MT")
    # do alag engine (1.5 NA vs 1.5 Turbo) me aata hai, alag price ke saath.
    # Bina engine ke naam collide hota tha aur DB me ek doosre ko overwrite karke
    # har sync me flip-flop (A->B->A) banata tha.
    parts = [p for p in [variant, engine, trans, edition] if p]
    return " ".join(parts).strip()


def _parse_variants(data, slug):
    out = []
    seen_names = set()
    if not isinstance(data, list):
        return out
    for v in data:
        price_str = v.get("price") or ""
        price = int(re.sub(r"[^\d]", "", price_str)) if price_str else None
        if price and 100000 < price < 15000000:
            name = _clean_variant(v)
            # safety: agar naam phir bhi repeat ho (koi aur field alag hai),
            # to price laga ke unique banao — taaki DB me overwrite na ho
            if name in seen_names:
                name = f"{name} ({price})"
            seen_names.add(name)
            out.append({
                "model": slug,
                "variant": name,
                "fuel_type": _detect_fuel(v),
                "ex_showroom_price": price,
            })
    return out


def scrape_hyundai():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 1. getModels
        try:
            page.goto(f"{API_BASE}/getModels?loc=IN&lan=en", timeout=40000)
            models = _json.loads(page.inner_text("body"))
        except Exception as e:
            print(f"  [Hyundai] getModels failed: {e}")
            browser.close()
            return []

        # 2. har model ke variants
        for m in models:
            desc = m.get("description", "")
            mid = m.get("id")
            if desc.upper() in SKIP_MODELS or not mid:
                continue
            slug = desc.lower().replace(" ", "-").replace("new-", "").strip("-")
            try:
                url = f"{API_BASE}/getPriceByModelAndCity?cityId={CITY_ID}&modelId={mid}&loc=IN&lan=en"
                page.goto(url, timeout=30000)
                body = page.inner_text("body")
                data = _json.loads(body)
                res = _parse_variants(data, slug)
                fuels = {}
                for r in res:
                    fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                breakdown = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                print(f"  [Hyundai] {desc}: {len(res)} variant(s)  [{breakdown}]")
                all_results.extend(res)
            except Exception as e:
                print(f"  [Hyundai] {desc} failed: {str(e)[:50]}")

        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_hyundai()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars[:60]:
        print(car)