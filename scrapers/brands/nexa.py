"""
scrapers/brands/nexa.py — Nexa scraper (DIRECT official pricing API)
====================================================================

Nexa ka official pricing API (Maruti jaisa, par channel=EXC aur nexa domain):

  GET: https://www.nexaexperience.com/pricing/v2/common/pricing/ex-showroom-detail
       ?forCode=08&channel=EXC&variantInfoRequired=true

Response: saare Nexa models ek call me — har variant exact price + naam + fuel.
  {"data":{"models":[
    {"modelCd":"BZ","modelDesc":"NEW BALENO","exShowroomDetailResponseDTOList":[
      {"variantDesc":"MARUTI BALENO SIGMA 1.2L ISS 5MT","exShowroomPrice":595200,
       "fuelTypeCd":"PET","colorType":"M"}, ...]}]}}

Note: har variant M/NM color ke liye 2 baar aata hai — dedup (lowest price).
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# Nexa pricing API — channel=EXC saare Nexa models deta hai (modelCodes ki zaroorat nahi)
PRICING_API = (
    "https://www.nexaexperience.com/pricing/v2/common/pricing/ex-showroom-detail"
    "?forCode=08&channel=EXC&variantInfoRequired=true"
)

# session/cookies ke liye ek Nexa page kholte hain
WARMUP_URL = "https://www.nexaexperience.com/baleno/price"

# model code -> display naam
MODEL_NAMES = {
    "BZ": "Baleno",
    "FR": "Fronx",
    "GV": "Grand Vitara",
    "JM": "Jimny",
    "XL": "XL6",
    "IN": "Invicto",
    "CI": "Ciaz",
    "VE": "e-Vitara",
    "IG": "Ignis",
}


def _detect_fuel(fuel_cd, variant_desc):
    f = (fuel_cd or "").upper()
    d = (variant_desc or "").upper()
    if "CNG" in f or "CNG" in d:
        return "CNG"
    if "DSL" in f or "DIESEL" in d:
        return "Diesel"
    # e-Vitara = electric (naam ya fuel code se)
    if "ELE" in f or "E VITARA" in d or "E-VITARA" in d or "EV DELTA" in d or "EV ALPHA" in d or "KWH" in d:
        return "Electric"
    if "HYB" in f or "HYBRID" in d:
        return "Hybrid"
    return "Petrol"


def _clean_variant(desc, model_name):
    """'MARUTI BALENO SIGMA 1.2L ISS 5MT' -> 'SIGMA 1.2L ISS 5MT'."""
    d = desc.strip()
    d = re.sub(r"(?i)^MARUTI\s+SUZUKI\s+", "", d)
    d = re.sub(r"(?i)^MARUTI\s+", "", d)
    # model naam ke shabd start se hata do (BALENO / GRAND VITARA / E VITARA / XL6)
    mwords = model_name.upper().replace("-", " ").split()
    dwords = d.split()
    idx = 0
    for mw in mwords:
        if idx < len(dwords) and dwords[idx].upper().replace("-", "") == mw.replace("-", ""):
            idx += 1
    if idx > 0:
        d = " ".join(dwords[idx:])
    return d.strip() or desc.strip()


def _parse_pricing(data):
    """pricing API JSON -> variant list. Dedup by (model,variant,fuel), lowest price."""
    best = {}
    models = data.get("data", {}).get("models", []) if isinstance(data, dict) else []
    for m in models:
        code = m.get("modelCd")
        model_name = MODEL_NAMES.get(code)
        if not model_name:
            continue
        for d in m.get("exShowroomDetailResponseDTOList", []):
            price = d.get("exShowroomPrice")
            desc = d.get("variantDesc", "")
            if not price or not desc:
                continue
            try:
                price = int(price)
            except Exception:
                continue
            if not (100000 < price < 30000000):
                continue
            variant = _clean_variant(desc, model_name)
            fuel = _detect_fuel(d.get("fuelTypeCd"), desc)
            key = (model_name, variant, fuel)
            if key not in best or price < best[key]["ex_showroom_price"]:
                best[key] = {
                    "model": model_name,
                    "variant": variant,
                    "fuel_type": fuel,
                    "ex_showroom_price": price,
                }
    return list(best.values())


def scrape_nexa():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            page.goto(WARMUP_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)

            data = None
            for attempt in range(3):
                try:
                    result = page.evaluate(
                        """async (url) => {
                            const r = await fetch(url, {headers: {'Content-Type':'application/json'}});
                            return await r.text();
                        }""",
                        PRICING_API,
                    )
                    data = _json.loads(result)
                    if data.get("data", {}).get("models"):
                        break
                except Exception:
                    page.wait_for_timeout(2000)

            if data:
                all_results = _parse_pricing(data)
                by_model = {}
                for r in all_results:
                    by_model.setdefault(r["model"], []).append(r)
                for mn, rows in by_model.items():
                    fuels = {}
                    for r in rows:
                        fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                    bd = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                    print(f"  [Nexa] {mn}: {len(rows)} variant(s)  [{bd}]")
            else:
                print("  [Nexa] pricing API nahi mila")
        except Exception as e:
            print(f"  [Nexa] failed: {str(e)[:60]}")
        finally:
            browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_nexa()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)