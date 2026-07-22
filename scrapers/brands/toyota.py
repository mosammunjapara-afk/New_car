"""
scrapers/brands/toyota.py — Toyota scraper (variants API via model page)
=========================================================================

Toyota ka data: webapi.tfsin.toyotabharat.com/1.0/api/cities/null/models/{id}/variants
Ye API seedha nahi khulta (session chahiye), isliye model page kholte hain
aur andar se jo /variants call hota hai use pakadte hain.

Data: name, price, formattedPrice, fuelType, transmissionType
"""

import json as _json
from playwright.sync_api import sync_playwright

# Toyota model pages (jinke andar se variants API call hota hai)
MODEL_PAGES = {
    "Glanza": "https://www.toyotabharat.com/showroom/glanza/",
    "Rumion": "https://www.toyotabharat.com/showroom/rumion/",
    "Innova Crysta": "https://www.toyotabharat.com/showroom/innova-crysta/",
    "Hilux": "https://www.toyotabharat.com/showroom/hilux/",
    "Vellfire": "https://www.toyotabharat.com/showroom/vellfire/",
    # NOTE: Camry aur Land Cruiser 300 hata diye — Toyota inki variant-price
    # online nahi deta (Camry single-config, Land Cruiser price-on-request
    # bespoke). Inke page pe /variants API fire hi nahi hota. Agar Toyota aage
    # inhe online kare, to wapas add kar sakte hain (Fortuner jaisa).
    "Fortuner": "https://www.toyotabharat.com/showroom/fortuner/index-fortuner.html",
    "Fortuner Legender": "https://www.toyotabharat.com/showroom/fortuner/index-legender.html",
    "Innova Hycross": "https://www.toyotabharat.com/showroom/innova/",
    "Urban Cruiser Hyryder": "https://www.toyotabharat.com/showroom/urbancruiser-hyryder/",
    "Taisor": "https://www.toyotabharat.com/showroom/urbancruiser-taisor/",
}


def _detect_fuel(v):
    f = (v.get("fuelType") or "").lower()
    if "diesel" in f:
        return "Diesel"
    if "cng" in f:
        return "CNG"
    if "electric" in f or "ev" in f:
        return "Electric"
    if "hybrid" in f:
        return "Hybrid"
    return "Petrol"


def _parse_variants(data, model_name):
    out = []
    variants = data.get("variants", []) if isinstance(data, dict) else []
    for v in variants:
        price = v.get("price")
        try:
            price = int(float(price)) if price else None
        except Exception:
            price = None
        if price and 100000 < price < 30000000:
            out.append({
                "model": model_name,
                "variant": v.get("name", "").strip(),
                "fuel_type": _detect_fuel(v),
                "ex_showroom_price": price,
            })
    return out


def scrape_toyota():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        captured = {"data": None}

        def on_response(resp):
            if "/variants" in resp.url and "toyotabharat" in resp.url:
                try:
                    captured["data"] = resp.json()
                except Exception:
                    pass

        page.on("response", on_response)

        for model_name, url in MODEL_PAGES.items():
            captured["data"] = None
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(6000)
                for _ in range(10):
                    page.mouse.wheel(0, 900)
                    page.wait_for_timeout(700)
                # API aane ka thoda aur wait
                for _ in range(6):
                    if captured["data"]:
                        break
                    page.wait_for_timeout(1500)

                if captured["data"]:
                    res = _parse_variants(captured["data"], model_name)
                    fuels = {}
                    for r in res:
                        fuels[r["fuel_type"]] = fuels.get(r["fuel_type"], 0) + 1
                    bd = ", ".join(f"{k}:{v}" for k, v in fuels.items())
                    print(f"  [Toyota] {model_name}: {len(res)} variant(s)  [{bd}]")
                    all_results.extend(res)
                else:
                    print(f"  [Toyota] {model_name}: 0 (API nahi pakda)")
            except Exception as e:
                print(f"  [Toyota] {model_name} failed: {str(e)[:50]}")

        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_toyota()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars[:40]:
        print(car)