"""
scrapers/brands/mercedes.py — Mercedes-Benz India scraper
==========================================================

Mercedes ka official vmos-api summary deta hai saare models + starting prices:
  https://api.oneweb.mercedes-benz.com/vmos-api/v1/data/IN/en/OWF/live/summary

Response: vehiclesData{} me har model:
  name                                  -> "C-Class", "GLA", "Mercedes-Maybach S-Class"
  bodytypeId                            -> saloon/offroader/coupe...
  technicalData.priceData.all.value     -> starting ex-showroom price

NOTE: Ye MODEL-level starting price hai (variant-wise nahi). Mercedes ka
variant catalog ek alag stock-based system me hai (dealer stock, incomplete).
Luxury ke liye model starting-price acceptable + official hai. Variant-detail
baad me add kar sakte hain.

Ye summary API page-load pe fire hoti hai (search-results page). Capture karke
parse karte hain.
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

SUMMARY_API = "https://api.oneweb.mercedes-benz.com/vmos-api/v1/data/IN/en/OWF/live/summary"
WARMUP_URL = "https://www.mercedes-benz.co.in/passengercars/buy/new-car/search-results.html/?emhsortType=price-asc&emhvehicleCategory=vehicles"


def _detect_fuel(name, bodytype):
    n = name.lower()
    if n.startswith("eq") or " eq" in n or "eqs" in n or "eqe" in n or "eqa" in n or "eqb" in n:
        return "Electric"
    # baaki Mercedes petrol/diesel dono, par starting mostly petrol
    return "Petrol"


def _parse_summary(data):
    best = {}  # model -> lowest-price row (ek model ka ek starting price)
    vd = data.get("vehiclesData", {}) if isinstance(data, dict) else {}
    for key, v in vd.items():
        if not isinstance(v, dict):
            continue
        name = v.get("name", "").strip()
        td = v.get("technicalData", {})
        price = td.get("priceData", {}).get("all", {}).get("value") if isinstance(td, dict) else None
        if not name or not price:
            continue
        try:
            price = int(price)
        except Exception:
            continue
        if not (2000000 < price < 100000000):
            continue
        model = re.sub(r"\s+", " ", name).strip()
        # same model ke multiple entries (variant/AMG) — sabse kam (starting) rakho
        if model not in best or price < best[model]["ex_showroom_price"]:
            best[model] = {
                "model": model,
                "variant": "Base",
                "fuel_type": _detect_fuel(model, v.get("bodytypeId", "")),
                "ex_showroom_price": price,
            }
    return list(best.values())


def scrape_mercedes():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.set_default_timeout(40000)

        captured = {"body": None}
        def on_response(resp):
            if "vmos-api" in resp.url and "summary" in resp.url:
                try:
                    captured["body"] = resp.text()
                except Exception:
                    pass
        page.on("response", on_response)

        try:
            page.goto(WARMUP_URL, wait_until="domcontentloaded", timeout=40000)
            for _ in range(10):
                page.wait_for_timeout(1200)
                if captured["body"]:
                    break
                try:
                    page.mouse.wheel(0, 900)
                except Exception:
                    pass
            if captured["body"]:
                data = _json.loads(captured["body"])
                all_results = _parse_summary(data)
                print(f"  [Mercedes] {len(all_results)} models (starting prices)")
            else:
                print("  [Mercedes] summary API nahi mila")
        except Exception as e:
            print(f"  [Mercedes] failed: {str(e)[:60]}")
        finally:
            browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_mercedes()
    print(f"\nTOTAL: {len(cars)}")
    for c in cars:
        print(c)