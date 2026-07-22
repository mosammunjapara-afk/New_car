"""
debug_cardekho8.py — CarDekho /variants page ka data (MIL GAYA!)
=================================================================
/skoda/kushaq/variants pe variantName + variantPrice hai (has:True).
Ab is page ka HTML le ke confirm karte hain ki Kushaq ke ASLI variants
(Classic, Signature, Active, Sportline...) exact price ke saath hain.

3 model cross-check: Kushaq, Swift, Creta

CHALAO:
    python debug_cardekho8.py

Ye banayega:
  - cardekho_variants_kushaq.html
  - cardekho_variants_swift.html
  - cardekho_variants_creta.html
  - cardekho_debug8.txt
Sab UPLOAD kar dena (khaas kar .html files).
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.cardekho.com"
MODELS = [
    ("Skoda Kushaq", "skoda", "kushaq"),
    ("Maruti Swift", "maruti-suzuki", "swift"),
    ("Hyundai Creta", "hyundai", "creta"),
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for name, make, model in MODELS:
        url = f"{BASE}/{make}/{model}/variants"
        log("\n" + "=" * 70)
        log(f"MODEL: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(4000)
            for _ in range(6):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            html = page.content()
            fname = f"cardekho_variants_{model}.html"
            with open(fname, "w", encoding="utf-8") as hf:
                hf.write(html)
            log(f"  HTML saved: {fname} ({len(html)} chars)")

            # variantName + variantPrice + fuel + transmission pairs
            # (JSON object me ye saath hote hain)
            objs = re.findall(r'\{[^{}]*"variantName"[^{}]*\}', html)
            log(f"  variant objects: {len(objs)}")
            seen = set()
            shown = 0
            for o in objs:
                vn = re.search(r'"variantName"\s*:\s*"([^"]+)"', o)
                vp = re.search(r'"variantPrice"\s*:\s*"([^"]+)"', o)
                mc = re.search(r'"minComparePrice"\s*:\s*(\d+)', o)
                fu = re.search(r'"fuelType"\s*:\s*"([^"]*)"', o)
                tr = re.search(r'"transmission\w*"\s*:\s*"([^"]*)"', o)
                if vn:
                    key = vn.group(1)
                    if key in seen:
                        continue
                    seen.add(key)
                    shown += 1
                    if shown > 30:
                        break
                    price = mc.group(1) if mc else (vp.group(1) if vp else "?")
                    fuel = fu.group(1) if fu else ""
                    trans = tr.group(1) if tr else ""
                    log(f"    {key}  |  ₹{price}  |  {fuel} {trans}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug8.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. Ye upload karo:")
print("  - cardekho_variants_kushaq.html (ZAROORI)")
print("  - cardekho_debug8.txt")
print("=" * 60)