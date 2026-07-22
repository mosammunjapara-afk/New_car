"""
debug_cardekho6.py — CarDekho MID se variant-price + poora HTML dump
=====================================================================
MID mil gaye (Kushaq=3625, Swift=3346). Ab 2 cheez:
  1. CarDekho ke known variant-price endpoints MID ke saath try karo
  2. /price page ka POORA rendered HTML ek file me save karo — taaki main
     offline usme variant+price exactly dhoondh sakoon (JS-render ke baad)

CHALAO:
    python debug_cardekho6.py

2 file banengi:
  - cardekho_debug6.txt  (endpoint results)
  - cardekho_kushaq.html (poora rendered HTML)
  - cardekho_swift.html
DONO/TEENO upload kar dena (html sabse important).
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.cardekho.com"
MODELS = [
    ("Skoda Kushaq", "skoda", "kushaq", "3625"),
    ("Maruti Swift", "maruti-suzuki", "swift", "3346"),
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def exact_prices(body):
    nums = re.findall(r'\b(\d{6,8})\b', body)
    return sorted(set(int(n) for n in nums if 100000 <= int(n) <= 99999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for name, make, model, mid in MODELS:
        log("\n" + "=" * 70)
        log(f"MODEL: {name}  (MID={mid})")
        log("=" * 70)

        # ---- 1. /price page kholo, variant table ko expand karo ----
        url = f"{BASE}/{make}/{model}/price"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            for _ in range(10):
                page.mouse.wheel(0, 1300)
                page.wait_for_timeout(500)

            # koi bhi "variant" / "view price" / "price breakup" / "+" expand dabao
            for label in ["View all variants", "All Variants", "Variants",
                          "View Price Breakup", "Price Breakup", "Show More",
                          "View More", "Compare Variants"]:
                try:
                    els = page.locator(f"text={label}")
                    n = els.count()
                    for i in range(min(n, 3)):
                        try:
                            els.nth(i).click(timeout=2000)
                            page.wait_for_timeout(1500)
                        except Exception:
                            pass
                except Exception:
                    pass
            page.wait_for_timeout(3000)
            for _ in range(5):
                page.mouse.wheel(0, 1300)
                page.wait_for_timeout(500)

            # ---- 2. poora HTML save karo ----
            html = page.content()
            fname = f"cardekho_{model}.html"
            with open(fname, "w", encoding="utf-8") as hf:
                hf.write(html)
            log(f"  HTML saved: {fname} ({len(html)} chars)")

            # quick check: HTML me variant + price hai?
            # CarDekho variant naam patterns: "1.0 TSI ..", "LXi", "VXi", "ZXi", trims
            vprice = re.findall(
                r'([A-Z][A-Za-z0-9.\s\-\+\(\)]{2,35}?)\s*(?:</[^>]+>\s*){0,3}(?:₹|Rs\.?)\s?([\d,]{4,})',
                html)
            if vprice:
                log(f"  HTML me variant+price patterns ({len(vprice)}):")
                shown = 0
                seen = set()
                for vn, pr in vprice:
                    vn = vn.strip()
                    key = vn[:20] + pr
                    if key in seen or len(vn) < 3:
                        continue
                    seen.add(key)
                    shown += 1
                    if shown > 25:
                        break
                    log(f"    {vn[:35]}  —  ₹{pr}")

            # ---- 3. rendered body text me variant lines ----
            txt = page.inner_text("body")
            # is model ki variant lines (naam + Lakh/₹), sidebar models chhod ke
            model_words = model.replace("-", " ").split()
            vlines = []
            for l in txt.split("\n"):
                l = l.strip()
                if re.search(r"(₹|Rs)\s?[\d,.]+", l) and 5 < len(l) < 60 \
                   and not any(w in l for w in ["Offers", "Lakh*", "onwards", "EMI", "Down"]):
                    vlines.append(l)
            seen = set(); uniq = []
            for l in vlines:
                if l[:30] not in seen:
                    seen.add(l[:30]); uniq.append(l)
            if uniq:
                log(f"  body variant-price lines ({len(uniq)}):")
                for l in uniq[:25]:
                    log(f"    {l[:60]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug6.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. Ye files upload karo:")
print("  - cardekho_kushaq.html   (SABSE ZAROORI)")
print("  - cardekho_swift.html")
print("  - cardekho_debug6.txt")
print("=" * 60)