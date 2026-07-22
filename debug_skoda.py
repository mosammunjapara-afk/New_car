"""
debug_skoda.py — Skoda ke price page ka structure + API dhoondo
================================================================
Skoda India ki site pe har car ka price page hota hai. Ye script har model ka
page khol ke dekhega:
  1. Page khula ya nahi (status)
  2. Koi JSON price API call hua ya nahi (variant + price)
  3. __NEXT_DATA__ / embedded data me variant-price hai kya
  4. Page pe dikhne wale ₹ prices

Sab skoda_debug.txt me save hoga.

CHALAO:
    python debug_skoda.py
Phir skoda_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

# Skoda India — models aur unke possible price-page URLs
# (alag-alag URL patterns try karenge, jo chale)
BASE = "https://www.skoda-auto.co.in"
MODELS = {
    "Kushaq": ["/models/kushaq/price", "/kushaq/price", "/models/kushaq"],
    "Slavia": ["/models/slavia/price", "/slavia/price", "/models/slavia"],
    "Kodiaq": ["/models/kodiaq/price", "/kodiaq/price", "/models/kodiaq"],
    "Kylaq":  ["/models/kylaq/price", "/kylaq/price", "/models/kylaq"],
}

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def looks_price(body):
    return bool(re.search(r'\d{6,7}', body)) and any(
        k in body.lower() for k in ["variant", "price", "grade", "trim", "exshowroom", "ex-showroom"]
    )


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    apis = []
    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["google","gtm","facebook","gstatic","fonts","youtube",
                                "analytics","clarity","adobe","demdex","omtrdc","cookie",
                                "onetrust","hotjar","bing","linkedin"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if looks_price(b):
                apis.append((u, b[:400]))

    page.on("response", on_response)

    for model, urls in MODELS.items():
        log("\n" + "=" * 70)
        log(f"MODEL: {model}")
        log("=" * 70)
        found_page = False
        for path in urls:
            url = BASE + path
            apis.clear()
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                st = resp.status if resp else "?"
                log(f"  [{st}] {url}")
                if st == 200:
                    found_page = True
                    page.wait_for_timeout(6000)
                    for _ in range(4):
                        page.mouse.wheel(0, 1200)
                        page.wait_for_timeout(600)
                    page.wait_for_timeout(2000)

                    # price APIs
                    if apis:
                        log(f"    --- price JSON APIs ({len(apis)}) ---")
                        seen = set()
                        for u, prev in apis:
                            base = u.split("?")[0]
                            if base in seen:
                                continue
                            seen.add(base)
                            log(f"    API: {u[:110]}")
                            log(f"         {prev[:250]}")

                    # __NEXT_DATA__
                    try:
                        nd = page.evaluate(
                            "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                        if nd and looks_price(nd):
                            log(f"    __NEXT_DATA__ me price data hai (len {len(nd)})")
                            # variant/price keys ke around dikhao
                            for kw in ['"price"', '"variant"', '"variants"', '"grade"', '"trim"', '"exShowroom"']:
                                i = nd.find(kw)
                                if i != -1:
                                    log(f"      near {kw}: {nd[max(0,i-20):i+200]}")
                    except Exception:
                        pass

                    # page ₹ prices
                    try:
                        txt = page.inner_text("body")
                        plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
                        if plines:
                            log(f"    Page ₹ prices ({len(plines)}):")
                            for l in plines[:15]:
                                log(f"      {l[:60]}")
                    except Exception:
                        pass
                    break  # ye URL chala, agla model
            except Exception as e:
                log(f"  goto fail {path}: {str(e)[:50]}")
        if not found_page:
            log("  (koi price-page URL nahi chala)")

    browser.close()

with open("skoda_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug.txt UPLOAD kar do.")
print("=" * 60)