"""
scrapers/brands/kia.py — Kia scraper (Playwright + text parsing)
=================================================================

Kia ke model page pe variant + starting price aise hote hain:
    HTE
    ₹ 10,99,900 Starting MSRP*
    HTK
    ₹ 13,41,900 Starting MSRP*

URL: https://www.kia.com/in/our-vehicles/{model}.html
Prices scroll ke baad load hoti hain. Text se parse karte hain (Maruti jaisa).

Note: ye "Starting MSRP" (har trim ka shuruaati price) deta hai.
"""

import re
from playwright.sync_api import sync_playwright

BASE = "https://www.kia.com/in/our-vehicles"

# Kia models (slug: display name)
MODELS = {
    "seltos": "Seltos",
    "sonet": "Sonet",
    "carens": "Carens",
    "carens-clavis": "Carens Clavis",
    "syros": "Syros",
    "carnival": "Carnival",
    "ev6": "EV6",
    "ev9": "EV9",
}

# Kia trim naam in se shuru hote hain
TRIMS = ("HTE", "HTK", "HTX", "GTX", "X LINE", "X-LINE", "GT",
         "Tech", "Prestige", "Premium", "Smart",
         # Carnival ka trim: "Limousine", "Limousine Plus"
         "Limousine",
         # EV9 ka trim: "GT-Line", "GT Line AWD"
         "GT-Line", "GT Line")


def _detect_fuel(model_slug, variant):
    # Kia EV models
    if model_slug in ("ev6", "ev9") or "ev" in model_slug:
        return "Electric"
    # Carnival India me sirf Diesel hai
    if model_slug == "carnival":
        return "Diesel"
    # baaki mostly petrol (diesel/turbo alag variant me aata hai, par MSRP starting petrol hai)
    v = variant.lower()
    if "diesel" in v or "d " in v:
        return "Diesel"
    return "Petrol"


def _parse_page(body_text, slug):
    lines = [l.strip() for l in body_text.split("\n") if l.strip()]
    results = []
    trims_upper = [t.upper() for t in TRIMS]
    i = 0
    while i < len(lines):
        line = lines[i]
        is_variant = (len(line) < 20 and any(line.upper().startswith(t) for t in trims_upper))
        if is_variant:
            variant = line
            price = None
            for j in range(i + 1, min(i + 4, len(lines))):
                pm = re.search(r"₹\s*([\d,]{5,}).*MSRP", lines[j])
                if not pm:
                    pm = re.search(r"₹\s*([\d,]{5,})", lines[j])
                if pm:
                    price = int(re.sub(r"[^\d]", "", pm.group(1)))
                    break
            if price and 100000 < price < 30000000:
                results.append({
                    "model": slug,
                    "variant": variant,
                    "fuel_type": _detect_fuel(slug, variant),
                    "ex_showroom_price": price,
                })
        i += 1
    # dedupe
    seen = set()
    uniq = []
    for r in results:
        k = (r["variant"], r["ex_showroom_price"])
        if k not in seen:
            seen.add(k)
            uniq.append(r)
    return uniq


def _scrape_one_model(page, slug):
    url = f"{BASE}/{slug}.html"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    for _ in range(8):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(600)
    page.wait_for_timeout(2000)
    body_text = page.inner_text("body")
    return _parse_page(body_text, slug)


def scrape_kia():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        for slug in MODELS:
            try:
                res = _scrape_one_model(page, slug)
                print(f"  [Kia] {slug}: {len(res)} variant(s)")
                all_results.extend(res)
            except Exception as e:
                print(f"  [Kia] {slug} failed: {str(e)[:50]}")
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_kia()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)