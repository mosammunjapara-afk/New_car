"""
scrapers/brands/lexus.py — Lexus India scraper
===============================================

Lexus model pages pe VARIANT-wise prices hain:
  "NX 350h Exquisite | Hybrid Electric | INR 67,59,000"
  "LX 500d Urban | Diesel | INR 2,81,40,000"

Har model page ka rendered text parse karke variant + fuel + price nikaalte hain.
Pattern: "<MODEL VARIANT> | <fuel> | INR <price>"
"""

import re
from playwright.sync_api import sync_playwright

BASE = "https://www.lexusindia.co.in"
MODEL_PAGES = [
    ("ES", f"{BASE}/models/es-350h/"),
    ("ES", f"{BASE}/models/es-500e/"),
    ("NX", f"{BASE}/models/nx/"),
    ("RX", f"{BASE}/models/rx/"),
    ("LX", f"{BASE}/models/lx/"),
    ("LM", f"{BASE}/models/lm/"),
]


def _detect_fuel(text):
    t = text.lower()
    if "full electric" in t or "500e" in t:
        return "Electric"
    if "diesel" in t:
        return "Diesel"
    if "hybrid" in t:
        return "Hybrid"
    return "Petrol"


def scrape_lexus():
    all_results = []
    seen = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)

        for model, url in MODEL_PAGES:
            try:
                print(f"  [Lexus] loading {url.split('/')[-2]} ...")
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                if not resp or resp.status != 200:
                    print(f"  [Lexus] {model}: status {resp.status if resp else '?'} skip")
                    continue
                page.wait_for_timeout(5000)
                # ₹/INR aane ka wait (max ~10s)
                for _ in range(10):
                    try:
                        body = page.inner_text("body")
                        if "INR" in body or "₹" in body:
                            break
                    except Exception:
                        pass
                    page.wait_for_timeout(1000)
                    try:
                        page.mouse.wheel(0, 1200)
                    except Exception:
                        pass
                page.wait_for_timeout(1500)

                txt = page.inner_text("body")
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                for i, l in enumerate(lines):
                    # price line
                    m = re.search(r"(INR|₹|Rs)\s*([\d,]+)", l)
                    if not m:
                        continue
                    # "From INR..." = model starting range, variant nahi — skip
                    if "from" in l.lower() or "starts" in l.lower():
                        continue
                    price = int(re.sub(r"[^\d]", "", m.group(2)))
                    if not (2000000 < price < 100000000):
                        continue
                    # structure: [i-2]=variant naam, [i-1]=fuel, [i]=price
                    vline = lines[i-2].strip() if i >= 2 else ""
                    fline = lines[i-1].strip() if i >= 1 else ""
                    # fuel line me fuel-word hona chahiye (warna ye variant-block nahi)
                    if not re.search(r"(?i)(hybrid|diesel|electric|petrol)", fline):
                        continue
                    # variant line valid? (naam, feature nahi)
                    if not vline or re.search(r"(?i)(view|explore|details|HP\b|from|inr|₹)", vline):
                        continue
                    if len(vline) > 45:
                        continue
                    fuel = _detect_fuel(fline)
                    # variant = model code hata ke (NX 350h Overtrail -> 350h Overtrail)
                    vv = re.sub(rf"^\s*{re.escape(model)}\s+", "", vline).strip()
                    if not vv or len(vv) < 2:
                        vv = vline
                    key = (model, vv, price)
                    if key in seen:
                        continue
                    seen.add(key)
                    all_results.append({
                        "model": model,
                        "variant": vv,
                        "fuel_type": fuel,
                        "ex_showroom_price": price,
                    })
            except Exception as e:
                print(f"  [Lexus] {model} fail: {str(e)[:40]}")

        # print summary
        by = {}
        for r in all_results:
            by.setdefault(r["model"], 0)
            by[r["model"]] += 1
        for m, c in by.items():
            print(f"  [Lexus] {m}: {c} variant(s)")
        if not all_results:
            print("  [Lexus] koi variant nahi mila")
        browser.close()
    return all_results


if __name__ == "__main__":
    cars = scrape_lexus()
    print(f"\nTOTAL: {len(cars)}")
    for c in cars:
        print(c)