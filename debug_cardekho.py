"""
debug_cardekho.py — CarDekho se exact per-variant price (clean JSON) test
==========================================================================
CarWale ne real prices diye par per-variant exact rupee clean API nahi mila.
CarDekho ka variant data aksar __NEXT_DATA__ / ek clean JSON API me hota hai
(exact price + fuel + transmission). Ye test karte hain.

3 model test: Skoda Kushaq (jo official chhupata), Maruti Swift + Hyundai Creta
(jinhe hum official se jaante hain → cross-check ke liye).

CHALAO:
    python debug_cardekho.py
Phir cardekho_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.cardekho.com"
TARGETS = [
    ("Skoda Kushaq", f"{BASE}/skoda/kushaq"),
    ("Maruti Swift", f"{BASE}/maruti-suzuki/swift"),
    ("Hyundai Creta", f"{BASE}/hyundai/creta"),
]

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing",
        "segment","taboola","criteo","crazyegg","moengage","clevertap","branch",
        "amazon-adsystem","scorecardresearch","cdn-cgi"]

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

    calls = []
    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            b = resp.text()
        except Exception:
            return
        if exact_prices(b) and any(k in b.lower() for k in
                ["variant","price","fuel","transmission","exshowroom"]):
            calls.append((u, resp.request.method, b))
    page.on("response", on_response)

    for name, url in TARGETS:
        calls.clear()
        log("\n" + "=" * 70)
        log(f"TARGET: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1400)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            # 1. __NEXT_DATA__ me variant+price?
            try:
                nd = page.evaluate(
                    "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
            except Exception:
                nd = ""
            if nd:
                gp = exact_prices(nd)
                log(f"  __NEXT_DATA__ len {len(nd)}, {len(gp)} exact-price numbers")
                if len(gp) >= 3:
                    log(f"    prices sample: {gp[:20]}")
                    # variant key ke around structure
                    for kw in ['"variantName"', '"variant_name"', '"variantList"',
                               '"variants"', '"priceValue"', '"price"', '"variantId"']:
                        i = nd.find(kw)
                        if i != -1:
                            log(f"    near {kw}: {nd[i:i+300]}")
                            break

            # 2. clean price JSON APIs
            hits = [(u, m, b, exact_prices(b)) for (u, m, b) in calls]
            hits.sort(key=lambda x: -len(x[3]))
            log(f"  price JSON APIs: {len(hits)}")
            seen = set()
            for u, m, b, gp in hits[:4]:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                log(f"\n  [{m}] {u[:120]}")
                log(f"  {len(gp)} exact prices: {gp[:15]}")
                log(f"  body: {b[:500].replace(chr(10),' ')}")

            # 3. page pe variant + price lines
            txt = page.inner_text("body")
            vlines = [l.strip() for l in txt.split("\n")
                      if re.search(r"(Classic|Signature|Active|Sportline|Prestige|Monte|"
                                   r"LXi|VXi|ZXi|Sigma|Delta|Zeta|Alpha|E |EX |SX |S\(O\))", l)
                      and ("₹" in l or "Rs" in l or "Lakh" in l)]
            if vlines:
                log(f"\n  variant+price lines ({len(vlines)}):")
                for l in vlines[:20]:
                    log(f"    {l[:70]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug.txt UPLOAD kar do.")
print("=" * 60)