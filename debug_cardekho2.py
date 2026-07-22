"""
debug_cardekho2.py — CarDekho ka EXACT per-variant price sub-page/API
=====================================================================
Main page pe summary ("11 variants from 10.69L") hai. Exact per-variant price
CarDekho ke /price ya variants sub-page me hota hai. Ye script:
  1. model page se andar ke variant/price links nikaalta hai
  2. /skoda/kushaq/price type page kholta hai
  3. Wahan __NEXT_DATA__ / embedded JSON me variant+exact price dhoondta hai
  4. page pe variant+₹ table bhi padhta hai

3 model cross-check: Kushaq, Swift, Creta

CHALAO:
    python debug_cardekho2.py
Phir cardekho_debug2.txt UPLOAD kar dena.
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


def exact_prices(body):
    nums = re.findall(r'\b(\d{6,8})\b', body)
    return sorted(set(int(n) for n in nums if 100000 <= int(n) <= 99999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for name, make, model in MODELS:
        # CarDekho ka price page: /make/model/price  (common pattern)
        candidates = [
            f"{BASE}/{make}/{model}/price",
            f"{BASE}/{make}/{model}/price-in-india",
            f"{BASE}/{make}/{model}#variants",
        ]
        log("\n" + "=" * 70)
        log(f"MODEL: {name}")
        log("=" * 70)
        for url in candidates:
            log(f"\n  TRY: {url}")
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                st = resp.status if resp else "?"
                log(f"    status: {st}")
                if st != 200:
                    continue
                page.wait_for_timeout(5000)
                for _ in range(6):
                    page.mouse.wheel(0, 1400)
                    page.wait_for_timeout(500)
                page.wait_for_timeout(2000)

                # __NEXT_DATA__ me variant+price
                nd = ""
                try:
                    nd = page.evaluate(
                        "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                except Exception:
                    pass
                # embedded json script tags bhi
                if not nd or len(exact_prices(nd)) < 3:
                    try:
                        scripts = page.evaluate("""() => {
                            return Array.from(document.querySelectorAll('script'))
                                .map(s => s.textContent).filter(t => t && t.length > 500);
                        }""")
                        # jisme sabse zyada exact-prices ho
                        best = ""
                        bestn = 0
                        for s in scripts:
                            n = len(exact_prices(s))
                            if n > bestn and any(k in s.lower() for k in ["variant","price"]):
                                bestn, best = n, s
                        if bestn >= 3:
                            nd = best
                    except Exception:
                        pass

                gp = exact_prices(nd) if nd else []
                if len(gp) >= 3:
                    log(f"    ✓ embedded JSON me {len(gp)} exact prices: {gp[:15]}")
                    # variant structure dikhao
                    for kw in ['"variantName"','"variant_name"','"variantList"',
                               '"variants"','"priceValue"','"price"','"name"']:
                        i = nd.find(kw)
                        if i != -1:
                            log(f"    near {kw}: {nd[i:i+280]}")
                            break

                # page pe variant + price
                txt = page.inner_text("body")
                vlines = [l.strip() for l in txt.split("\n")
                          if re.search(r"\b(Classic|Signature|Active|Sportline|Prestige|Monte|"
                                       r"LXi|VXi|ZXi|Sigma|Delta|Zeta|Alpha|E|S|SX|EX)\b", l)
                          and re.search(r"(₹|Rs|Lakh|\d{6,})", l)]
                seen = set()
                uniq = []
                for l in vlines:
                    if l[:40] not in seen:
                        seen.add(l[:40]); uniq.append(l)
                if uniq:
                    log(f"    variant+price lines ({len(uniq)}):")
                    for l in uniq[:25]:
                        log(f"      {l[:75]}")
                if len(gp) >= 3 or uniq:
                    break  # is model ke liye mil gaya
            except Exception as e:
                log(f"    fail: {str(e)[:50]}")

    browser.close()

with open("cardekho_debug2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug2.txt UPLOAD kar do.")
print("=" * 60)