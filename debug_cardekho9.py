"""
debug_cardekho9.py — CarDekho internal variant-API (token ke saath) pakdo
==========================================================================
2 BADE UNLOCK mile HTML se:
  - window.__CD_DATA__ = saare brands+models list (MID, slug)
  - window.__token = JWT auth token (internal API ke liye)

CarDekho variant data ek internal API se aata hai (browser me chalti hai, HTML
me nahi). Ye script:
  1. Swift page live kholta hai
  2. Us page pe har XHR/fetch (browser ka apna) intercept karta hai — poora URL
     + method + body, TAAKI variant-API ka exact endpoint mile
  3. Saath hi window.__token aur __CD_DATA__ (model list) nikaalta hai

Is baar hum har request (json ho ya na ho) capture karenge jinme model/variant/
price/mid ho — including staticcont/pwa bundle ke andar se jaane wali API calls.

CHALAO:
    python debug_cardekho9.py
Phir cardekho_debug9.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.cardekho.com"
URL = f"{BASE}/maruti-suzuki/swift/variants"

SKIP_DOM = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
            "clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing","taboola",
            "criteo","crazyegg","vdo.ai","performoo","moengage","clevertap","branch",
            "scorecardresearch","amazon-adsystem","tags3","imasdk","recaptcha",
            "connecto"]

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

    reqs = []  # (method, url, post_body)
    def on_request(req):
        u = req.url
        if any(s in u.lower() for s in SKIP_DOM):
            return
        # sirf XHR/fetch (document/image nahi)
        if req.resource_type not in ("xhr", "fetch"):
            return
        reqs.append((req.method, u, req.post_data or ""))
    page.on("request", on_request)

    price_resps = []  # (url, body) jinme exact price ho
    def on_response(resp):
        u = resp.url
        if any(s in u.lower() for s in SKIP_DOM):
            return
        if resp.request.resource_type not in ("xhr", "fetch"):
            return
        try:
            b = resp.text()
        except Exception:
            return
        # Swift-range exact prices (400000-1500000) + variant word
        nums = [int(x) for x in re.findall(r'\b(\d{6,7})\b', b) if 400000 <= int(x) <= 1500000]
        if len(nums) >= 3 or ('"variant' in b.lower() and re.search(r'\d{6}', b)):
            price_resps.append((u, b))
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(4000)
    # variant section tak scroll (API trigger ho)
    for _ in range(14):
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(500)
    page.wait_for_timeout(4000)

    # ---- token + model list ----
    try:
        token = page.evaluate("() => window.__token || ''")
        log(f"\n__token: {token[:60]}... (len {len(token)})")
    except Exception:
        token = ""
    try:
        cd = page.evaluate("() => JSON.stringify(window.__CD_DATA__ || {})")
        log(f"__CD_DATA__ len: {len(cd)}")
        # kitne models?
        mids = re.findall(r'"MID":"(\d+)"', cd)
        log(f"  total models in CD_DATA: {len(mids)}")
    except Exception:
        pass

    # ---- saare XHR/fetch endpoints ----
    log(f"\n=== XHR/fetch requests ({len(reqs)}) ===")
    seen = set()
    for m, u, body in reqs:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        log(f"  [{m}] {u[:120]}")
        if body:
            log(f"       body: {body[:150]}")

    # ---- price-jaisi responses ----
    log(f"\n=== responses with exact prices ({len(price_resps)}) ===")
    for u, b in price_resps[:5]:
        log(f"\n  URL: {u[:120]}")
        # variant name+price nikaalo
        names = re.findall(r'"variant\w*[Nn]ame"\s*:\s*"([^"]{2,45})"', b)
        prices = sorted(set(int(x) for x in re.findall(r'\b(\d{6,7})\b', b) if 300000 <= int(x) <= 1500000))
        log(f"    variant names: {names[:15]}")
        log(f"    exact prices: {prices[:15]}")
        log(f"    body sample: {b[:400].replace(chr(10),' ')}")

    browser.close()

with open("cardekho_debug9.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug9.txt UPLOAD kar do.")
print("=" * 60)