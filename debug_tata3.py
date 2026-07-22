"""
debug_tata3.py — Nexon ke saare variants nikaalne ki koshish
=============================================================
Page pe filter (Petrol/Diesel/CNG + edition) hai, isliye ek baar me kam
variants dikhte hain. Ye script 2 cheezein try karti hai:
  1. Filter buttons click karke saare fuel types ke variants
  2. Alag URL patterns (ev, etc.)
"""
from playwright.sync_api import sync_playwright
import re

URL = "https://cars.tatamotors.com/nexon/ice/price.html"

def extract_variants(page):
    """Page se abhi jo variants dikh rahe hain wo nikaalo."""
    txt = page.inner_text("body")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    out = []
    i = 0
    while i < len(lines):
        if i+1 < len(lines) and lines[i+1] == "Price *":
            variant = lines[i]
            price = None
            for j in range(i+2, min(i+4, len(lines))):
                pm = re.search(r"₹\s*([\d,]{4,})", lines[j])
                if pm:
                    price = int(re.sub(r"[^\d]", "", pm.group(1)))
                    break
            if price and 100000 < price < 5000000:
                out.append((variant, price))
        i += 1
    return out

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)

    all_variants = {}

    # Default view
    for v, pr in extract_variants(page):
        all_variants[v] = pr
    print(f"Default view: {len(all_variants)} variants")

    # Ab filter buttons dhoondh ke click karte hain: Petrol, Diesel, Bi-fuel CNG
    for fuel_btn in ["Diesel", "Bi-fuel CNG", "Petrol"]:
        try:
            # button text se click
            btn = page.get_by_text(fuel_btn, exact=True).first
            btn.click(timeout=5000)
            page.wait_for_timeout(3000)
            for _ in range(4):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            before = len(all_variants)
            for v, pr in extract_variants(page):
                all_variants[v] = pr
            print(f"'{fuel_btn}' click ke baad: +{len(all_variants)-before} naye (total {len(all_variants)})")
        except Exception as e:
            print(f"'{fuel_btn}' click nahi hua: {str(e)[:50]}")

    print(f"\n=== KUL {len(all_variants)} NEXON VARIANTS ===")
    for v, pr in sorted(all_variants.items(), key=lambda x: x[1]):
        print(f"  {v:20s} | Rs {pr:,}")

    browser.close()
    print("\nDONE.")