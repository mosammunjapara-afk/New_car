"""
scrapers/brands/volkswagen.py — Volkswagen India scraper
=========================================================

VW ka official variant-price API (har model page pe fire hota hai):
  https://v1-...-.mofa.feature-app.io/bff/model-overview?countryCode=IN&currency=INR&...

Response structure:
  payload.models[0].data.name            -> carline naam (The new Taigun)
  payload.models[0].children[i]          -> har variant (trim)
    .data.name                           -> variant naam (Comfortline - 1.0L TSI MT)
    .data.engines[0].prices.price1.value -> exact ex-showroom price

Har model page khol ke ye JSON capture karte hain (URL hi model-specific hai).
VW India sab petrol (TSI) hai.
"""

import re
import json as _json
from playwright.sync_api import sync_playwright

# VW India model pages (jinke andar model-overview API fire hota hai)
# NOTE: virtus.html ek master/landing page hai jahan API fire nahi hoti.
# Virtus ka asli variant data virtus-chrome.html + virtus-sport.html pe hai.
MODEL_PAGES = {
    "Taigun": "https://www.volkswagen.co.in/en/models/taigun.html",
    "Virtus": "https://www.volkswagen.co.in/en/models/virtus-chrome.html",
    "Virtus GT": "https://www.volkswagen.co.in/en/models/virtus-sport.html",
    # Tiguan R-Line aur Golf GTI single-variant premium CBU imports hain
    # (ek hi price, API fire nahi hoti). Filhaal chhod diya — agar VW inhe
    # multi-variant kare to add kar sakte hain.
}


def _detect_fuel(variant_name, carline):
    v = (variant_name + " " + carline).lower()
    if "diesel" in v or "tdi" in v:
        return "Diesel"
    if "electric" in v or " ev" in v:
        return "Electric"
    # VW India: TSI = petrol turbo
    return "Petrol"


def _clean_variant(name, slug):
    """variant naam clean karo. name='Comfortline - 1.0L TSI MT' ya slug se."""
    n = (name or "").strip()
    if not n and slug:
        # slug se: comfortline-1l-tsi-mt -> Comfortline 1L TSI MT
        n = slug.replace("-", " ").title()
        n = re.sub(r"\bTsi\b", "TSI", n)
        n = re.sub(r"\bMt\b", "MT", n)
        n = re.sub(r"\bAt\b", "AT", n)
    # extra spaces/dashes saaf
    n = re.sub(r"\s*-\s*", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _parse_overview(data, model_name):
    """model-overview JSON se variants nikaalo."""
    out = []
    seen = set()
    payload = data.get("payload", data) if isinstance(data, dict) else {}
    models = payload.get("models", [])
    for model in models:
        carline = model.get("data", {}).get("name", model_name)
        for ch in model.get("children", []):
            if ch.get("type") != "trim":
                # kabhi trim ke andar aur nesting — handle
                pass
            node = ch.get("nodeId", "")
            slug = node.split("/")[-1] if node else ""
            cd = ch.get("data", {})
            name = cd.get("name") or slug
            # price: engines[0].prices.price1.value ya referenceModel
            price = None
            engines = cd.get("engines", [])
            if engines:
                price = engines[0].get("prices", {}).get("price1", {}).get("value")
            if not price:
                price = cd.get("referenceModel", {}).get("prices", {}).get("price1", {}).get("value")
            if not price:
                continue
            try:
                price = int(price)
            except Exception:
                continue
            if not (200000 < price < 30000000):
                continue
            variant = _clean_variant(name, slug)
            fuel = _detect_fuel(variant, carline)
            key = (variant, price)
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


def scrape_volkswagen():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        captured = {"body": None}
        def on_response(resp):
            u = resp.url
            if "model-overview" not in u:
                return
            ct = resp.headers.get("content-type", "")
            if "json" not in ct:
                return
            try:
                b = resp.text()
                if '"payload"' in b and '"models"' in b:
                    captured["body"] = b
            except Exception:
                pass
        page.on("response", on_response)

        for model_name, url in MODEL_PAGES.items():
            captured["body"] = None
            res = []
            for attempt in range(2):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(5000)
                    for _ in range(6):
                        page.mouse.wheel(0, 1200)
                        page.wait_for_timeout(500)
                    # API aane ka wait
                    for _ in range(6):
                        if captured["body"]:
                            break
                        page.wait_for_timeout(1500)
                    if captured["body"]:
                        data = _json.loads(captured["body"])
                        res = _parse_overview(data, model_name)
                        if res:
                            break
                except Exception as e:
                    if attempt == 1:
                        print(f"  [VW] {model_name} failed: {str(e)[:50]}")
                captured["body"] = None
                page.wait_for_timeout(1500)

            if res:
                print(f"  [VW] {model_name}: {len(res)} variant(s)")
                all_results.extend(res)
            else:
                print(f"  [VW] {model_name}: 0 (API nahi mila)")

        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_volkswagen()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)