"""
debug_cardekho3.py — CarDekho variant-price: ld+json + price table rows
========================================================================
Pichhle 23 numbers tracking-template the (variantName khaali). Asli variant
table alag hai. Ye script 2 pakke source try karta hai:

  1. <script type="application/ld+json"> structured data (Google ke liye) —
     ismein aksar har variant ka naam + exact price hota hai (clean)
  2. Price table ke rows — har <tr>/<li> jisme variant naam + ₹ price ek saath ho

3 model cross-check: Kushaq, Swift, Creta

CHALAO:
    python debug_cardekho3.py
Phir cardekho_debug3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

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
        url = f"{BASE}/{make}/{model}/price"
        log("\n" + "=" * 70)
        log(f"MODEL: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0, 1400)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            # ---- 1. ld+json structured data ----
            ldjsons = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                    .map(s => s.textContent);
            }""")
            log(f"\n  ld+json blocks: {len(ldjsons)}")
            for i, lj in enumerate(ldjsons):
                if not lj:
                    continue
                try:
                    data = json.loads(lj)
                except Exception:
                    continue
                # dhoondo: offers / itemListElement / variant
                s = json.dumps(data)
                if any(k in s for k in ["offers", "Offer", "price", "Product", "Car"]):
                    log(f"  ld+json[{i}] (price-related, {len(s)} chars):")
                    log(f"    {s[:700]}")

            # ---- 2. price table rows (variant naam + ₹) ----
            rows = page.evaluate(r"""() => {
                const out = [];
                // table rows aur list items dono
                const els = Array.from(document.querySelectorAll('tr, li, div'));
                for (const el of els) {
                    const t = (el.innerText || '').trim().replace(/\s+/g,' ');
                    // variant naam + price ek hi row me (chhota row, ₹/Rs + digits)
                    if (t.length < 90 && /(₹|Rs\.?)\s?[\d,.]+/.test(t)
                        && /[A-Za-z]{3}/.test(t)) {
                        out.push(t);
                    }
                }
                return out;
            }""")
            # dedupe
            seen = set(); uniq = []
            for r in rows:
                k = r[:50]
                if k not in seen:
                    seen.add(k); uniq.append(r)
            log(f"\n  price-table rows ({len(uniq)}):")
            for r in uniq[:35]:
                log(f"    {r[:75]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug3.txt UPLOAD kar do.")
print("=" * 60)