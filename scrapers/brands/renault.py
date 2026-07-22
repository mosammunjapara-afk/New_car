"""
scrapers/brands/renault.py — Renault India scraper
===================================================

Renault India apni site pe VERSION-wise (trim) prices deti hai. Model page pe
"versions" section me har version ka starting price hota hai:
  Kiger: Authentic 5.81L, Evolution 6.55L, Evolution+ 6.99L, Techno 7.55L, Emotion 8.45L

Hum model page ka rendered text padhte hain aur "versions" ke neeche
'<version-name> ... *starting from ₹X' pattern se version+price nikaalte hain.

Renault trims (versions): Authentic, Evolution, Evolution+, Techno, Emotion,
Climber (Kwid), + variations.
"""

import re
from playwright.sync_api import sync_playwright

MODEL_PAGES = {
    "Kwid": "https://www.renault.co.in/cars/renault-kwid.html",
    "Kiger": "https://www.renault.co.in/cars/renault-kiger.html",
    "Triber": "https://www.renault.co.in/cars/renault-triber.html",
    "Duster": "https://www.renault.co.in/cars/renault-duster.html",
}

# Renault version (trim) naam — inhe variant maana jayega
VERSIONS = ["Authentic", "Evolution+", "Evolution", "Techno", "Emotion",
            "Climber", "RXE", "RXL", "RXT", "RXZ", "RXT(O)"]


def _detect_fuel(model, variant):
    v = (model + " " + variant).lower()
    if "diesel" in v:
        return "Diesel"
    if "cng" in v:
        return "CNG"
    # NOTE: "electric"/"ev" check hata diya — "Evolution" me 'ev' aata hai jo
    # galti se Electric detect karta tha. Renault India ke Kwid/Kiger/Triber/
    # Duster sab PETROL hain (koi EV model abhi nahi). Jab Renault EV laaye
    # (jaise future models), tab model naam se add kar sakte hain.
    return "Petrol"


def _scrape_one_model(page, model_name, url):
    results = []
    seen = set()
    page.goto(url, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(5000)
    for _ in range(8):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(500)
    page.wait_for_timeout(2000)

    txt = page.inner_text("body")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]

    # pattern: line me version naam, agli ya usi ke aas-paas "*starting from ₹X"
    # hum har ₹-price line ke 1-2 line upar version dhoondte hain
    for i, l in enumerate(lines):
        if "starting from" in l.lower() and "₹" in l:
            # price nikaalo
            m = re.search(r"₹\s*([\d,]+)", l)
            if not m:
                continue
            price = int(re.sub(r"[^\d]", "", m.group(1)))
            if not (100000 < price < 5000000):
                continue
            # version naam: upar wali 1-2 lines me
            version = None
            for j in (i-1, i-2, i):
                if 0 <= j < len(lines):
                    cand = lines[j].strip()
                    for v in VERSIONS:
                        if cand.lower() == v.lower() or cand.lower().startswith(v.lower()):
                            version = v
                            break
                    if version:
                        break
            if not version:
                continue
            key = (version, price)
            if key in seen:
                continue
            seen.add(key)
            results.append({
                "model": model_name,
                "variant": version,
                "fuel_type": _detect_fuel(model_name, version),
                "ex_showroom_price": price,
            })
    return results


def scrape_renault():
    all_results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        for model_name, url in MODEL_PAGES.items():
            res = []
            for attempt in range(2):
                try:
                    res = _scrape_one_model(page, model_name, url)
                    if res:
                        break
                except Exception as e:
                    if attempt == 1:
                        print(f"  [Renault] {model_name} failed: {str(e)[:50]}")
                page.wait_for_timeout(2000)
            print(f"  [Renault] {model_name}: {len(res)} version(s)")
            all_results.extend(res)
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_renault()
    print(f"\nTOTAL: {len(cars)} variants")
    for car in cars:
        print(car)