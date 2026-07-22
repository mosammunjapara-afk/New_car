"""
scrapers/brands/cardekho_source.py — CarDekho-based scraper (blocked brands)
=============================================================================

Kuch brands (Mahindra naye models, Audi, Volvo, Skoda) apni OFFICIAL site se
automatic variant-price nahi dete (JS-encrypted / bot-block). In ke liye
CarDekho ka structured-data (JSON-LD Product) use karte hain — ye AUTOMATIC
auto-update hota hai (CarDekho roz refresh karta hai), variant-wise EX-SHOWROOM.

Structure (CarDekho model page HTML me JSON-LD):
  "name":"<Brand> <Model> <Variant>", ... "brand":{"name":"<Brand>"}, ...
  "offers":{..."price":"<ex-showroom>"...}

Har model page: https://www.cardekho.com/{brand-slug}/{model-slug}
"""

import re
from playwright.sync_api import sync_playwright

# blocked brands ke models jo CarDekho se laane hain
# format: (Brand display, model display, cardekho_url)
CARDEKHO_MODELS = [
    # Mahindra naye models (XUV700 official se aata hai, ye naye)
    ("Mahindra", "Thar", "https://www.cardekho.com/mahindra/thar"),
    ("Mahindra", "Thar Roxx", "https://www.cardekho.com/mahindra/thar-roxx"),
    ("Mahindra", "Scorpio N", "https://www.cardekho.com/mahindra/scorpio-n"),
    ("Mahindra", "Scorpio Classic", "https://www.cardekho.com/mahindra/scorpio-classic"),
    ("Mahindra", "XUV 3XO", "https://www.cardekho.com/mahindra/xuv-3xo"),
    ("Mahindra", "Bolero", "https://www.cardekho.com/mahindra/bolero"),
    ("Mahindra", "Bolero Neo", "https://www.cardekho.com/mahindra/bolero-neo"),
    ("Mahindra", "BE 6", "https://www.cardekho.com/mahindra/be-6"),
    ("Mahindra", "XEV 9e", "https://www.cardekho.com/mahindra/xev-9e"),
    # Audi
    ("Audi", "A4", "https://www.cardekho.com/audi/a4"),
    ("Audi", "A6", "https://www.cardekho.com/audi/a6"),
    ("Audi", "Q3", "https://www.cardekho.com/audi/q3"),
    ("Audi", "Q5", "https://www.cardekho.com/audi/q5"),
    ("Audi", "Q7", "https://www.cardekho.com/audi/q7"),
    ("Audi", "Q8", "https://www.cardekho.com/audi/q8"),
    # Volvo (XC40 -> xc40-recharge, S90 discontinued India)
    ("Volvo", "XC40", "https://www.cardekho.com/volvo/xc40-recharge"),
    ("Volvo", "XC60", "https://www.cardekho.com/volvo/xc60"),
    ("Volvo", "XC90", "https://www.cardekho.com/volvo/xc90"),
    ("Volvo", "C40 Recharge", "https://www.cardekho.com/volvo/c40-recharge"),
    # Skoda
    ("Skoda", "Kushaq", "https://www.cardekho.com/skoda/kushaq"),
    ("Skoda", "Slavia", "https://www.cardekho.com/skoda/slavia"),
    ("Skoda", "Kodiaq", "https://www.cardekho.com/skoda/kodiaq"),
    ("Skoda", "Kylaq", "https://www.cardekho.com/skoda/kylaq"),
]


def _detect_fuel(variant_name):
    v = variant_name.lower()
    if "diesel" in v:
        return "Diesel"
    if "electric" in v or "ev" in v.split() or "e-tron" in v or "recharge" in v or "kwh" in v:
        return "Electric"
    if "cng" in v:
        return "CNG"
    if "hybrid" in v:
        return "Hybrid"
    return "Petrol"


def _parse_html(html, brand, model):
    """CarDekho JSON-LD Product blocks se variant + ex-showroom nikaalo."""
    out = []
    seen = set()
    # "name":"Brand Model Variant" ... "price":"NNNN"  (brand block beech me aata hai)
    prefix = f"{brand} {model}"
    pattern = r'"name":"(' + re.escape(brand) + r'[^"]*)".*?"price":"(\d{6,8})"'
    for name, pr in re.findall(pattern, html):
        price = int(pr)
        if not (200000 < price < 90000000):
            continue
        # CarDekho kabhi ₹1 ka rounding-diff deta hai (2190000 vs 2190001) jo
        # har sync me flip-flop dikhata hai. Nearest 100 pe round karo (ex-showroom
        # hamesha round hota hai) taaki data stable rahe.
        price = round(price / 100) * 100
        # junk lines skip
        if "Price" in name and ("Image" in name or "Review" in name or "Colour" in name):
            continue
        # variant = naam me se "Brand Model" hata ke
        variant = name
        variant = re.sub(re.escape(prefix), "", variant, flags=re.I).strip()
        # kabhi model naam thoda alag (Scorpio N vs Scorpio-N) — model words hata
        for w in model.split():
            variant = re.sub(r"(?i)^" + re.escape(w) + r"\s+", "", variant).strip()
        # brand naam akela bacha (base product) ya khaali -> Base
        if not variant or variant.lower() == brand.lower():
            variant = "Base"
        if len(variant) > 45 or "Image" in variant or "Review" in variant:
            continue
        fuel = _detect_fuel(name)
        key = (variant, price)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "model": model,
            "variant": variant,
            "fuel_type": fuel,
            "ex_showroom_price": price,
        })
    return out


def scrape_from_cardekho(brand_filter=None):
    """
    brand_filter: agar diya (e.g. "Audi") to sirf us brand ke models.
    Return: list of car dicts (model/variant/fuel/price).
    """
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-IN",
        )
        context.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = context.new_page()
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)

        for brand, model, url in CARDEKHO_MODELS:
            if brand_filter and brand != brand_filter:
                continue
            try:
                r = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if not r or r.status != 200:
                    print(f"  [CarDekho] {brand} {model}: status {r.status if r else '?'}")
                    continue
                page.wait_for_timeout(3500)
                for _ in range(4):
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(400)
                html = page.content()
                rows = _parse_html(html, brand, model)
                if rows:
                    print(f"  [CarDekho] {brand} {model}: {len(rows)} variant(s)")
                    results.extend(rows)
                else:
                    print(f"  [CarDekho] {brand} {model}: 0")
            except Exception as e:
                print(f"  [CarDekho] {brand} {model} fail: {str(e)[:40]}")
        browser.close()
    return results


if __name__ == "__main__":
    import sys
    bf = sys.argv[1] if len(sys.argv) > 1 else None
    cars = scrape_from_cardekho(bf)
    print(f"\nTOTAL: {len(cars)}")
    for c in cars[:60]:
        print(c)