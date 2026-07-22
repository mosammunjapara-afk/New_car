"""
scrapers/brands/citroen.py — Citroen India scraper (DIRECT official API)
========================================================================

Citroen ka official configurator API (page-load pe fire hota hai; direct fetch
401 deta hai isliye page ke through capture karte hain):

  model list:  configuratorapi.citroen.in/api/v1/model/all?lang_code=en-IN
  variants:    configuratorapi.citroen.in/api/v1/variants/all?model_id=X&lang_code=en-IN

Response: response.model_name + response.variants[] with:
  variant_name  -> "PLUS TURBO"
  variant_desc  -> "CC22 1.2P TURBO AT PLUS" (isme transmission/fuel)
  price         -> exact ex-showroom

Duplicate naam (PLUS TURBO MT vs AT) ko desc ke transmission se alag karte hain.
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# Citroen model pages (jinke load pe API fire hoti hai). model_id 1-5.
MODEL_PAGES = [
    "https://www.citroen.in/models/basalt.html",
    "https://www.citroen.in/models/c3.html",
    "https://www.citroen.in/models/aircross.html",
    "https://www.citroen.in/models/new-e-c3.html",
    "https://www.citroen.in/models/c5-aircross.html",
]

# model_id -> clean display naam (API ke model_name se bhi le sakte)
MODEL_NAME_FIX = {
    "Basalt": "Basalt",
    "C3": "C3",
    "AirCross": "C3 Aircross",
    "C5 AirCross": "C5 Aircross",
    "Ë-C3": "e-C3",
}


def _detect_fuel(model_name, variant_desc):
    m = model_name.lower()
    d = (variant_desc or "").upper()
    if m.startswith("e-") or m.startswith("ë-") or "e-c3" in m or "electric" in m:
        return "Electric"
    if "DIESEL" in d or "BLUEHDI" in d or "1.5D" in d:
        return "Diesel"
    return "Petrol"


def _clean_variant(v):
    """
    variant_name + transmission_code + seats taaki har variant UNIQUE + stable ho.
    Citroen API me variant_desc/transmission_type khaali hote hain, par
    transmission_code (AT/MT) aur num_of_seats (5/7 Seater) bhare hote hain.
    'MAX TURBO' + AT + 7 Seater -> 'Max Turbo AT 7-Seater'
    """
    name = (v.get("variant_name") or "").strip().title()
    tc = (v.get("transmission_code") or "").strip().upper()
    if tc in ("AT", "MT", "CVT", "DCT") and tc.lower() not in name.lower().split():
        name = f"{name} {tc}"
    seats = (v.get("num_of_seats") or "").strip()  # "7 Seater"
    sm = re.search(r"(\d+)", seats)
    if sm and sm.group(1) not in name:
        name = f"{name} {sm.group(1)}-Seater"
    name = re.sub(r"(?i)\bturbo\b", "Turbo", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _parse_model(resp_json):
    """ek model ki API response se variants nikaalo."""
    out = []
    seen = set()
    r = resp_json.get("response", {}) if isinstance(resp_json, dict) else {}
    raw_model = r.get("model_name", "")
    model_name = MODEL_NAME_FIX.get(raw_model, raw_model)
    for v in r.get("variants", []):
        if not isinstance(v, dict):
            continue
        vname = v.get("variant_name", "")
        vdesc = v.get("variant_desc", "")
        price = v.get("price")
        if not vname or not price:
            continue
        try:
            price = int(price)
        except Exception:
            continue
        if not (100000 < price < 30000000):
            continue
        variant = _clean_variant(v)
        fuel = _detect_fuel(model_name, vdesc)
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


def scrape_citroen():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.set_default_timeout(40000)
        page.set_default_navigation_timeout(40000)

        variants_captured = {}  # model_id -> response text
        def on_response(resp):
            u = resp.url
            if "configuratorapi.citroen.in/api/v1/variants/all" in u:
                mid = re.search(r"model_id=(\d+)", u)
                if mid:
                    try:
                        variants_captured[mid.group(1)] = resp.text()
                    except Exception:
                        pass
        page.on("response", on_response)

        for url in MODEL_PAGES:
            try:
                print(f"  [Citroen] loading {url.split('/')[-1]} ...")
                page.goto(url, wait_until="domcontentloaded", timeout=40000)
                # API aane ka wait (max ~12s), warna aage badho
                for _ in range(12):
                    page.wait_for_timeout(1000)
                    # thoda scroll (lazy trigger)
                    try:
                        page.mouse.wheel(0, 800)
                    except Exception:
                        pass
            except Exception as e:
                print(f"  [Citroen] {url.split('/')[-1]} fail: {str(e)[:40]}")
                continue

        # parse captured
        by_model = {}
        for mid, body in variants_captured.items():
            try:
                data = _json.loads(body)
                rows = _parse_model(data)
                for r in rows:
                    by_model.setdefault(r["model"], []).append(r)
                all_results.extend(rows)
            except Exception:
                pass

        for mn, rows in by_model.items():
            print(f"  [Citroen] {mn}: {len(rows)} variant(s)")
        if not all_results:
            print("  [Citroen] koi variant nahi mila")

        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_citroen()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)