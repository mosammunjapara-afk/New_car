"""
debug_landrover2.py — Land Rover pricing API / configure page dhoondo
======================================================================
Homepage se sirf defender/discovery mile. Range Rover models alag hain.
Ye script har LR model page khol ke:
  1. andar ke price/configure/specifications links nikaalta hai
  2. koi pricing API (JSON) capture karta hai
  3. page pe ₹ prices dhoondta hai
  4. known LR model URLs try karta hai

CHALAO:
    python debug_landrover2.py
Phir landrover2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.landrover.in"
# LR India ke known model pages
MODELS = [
    "https://www.landrover.in/range-rover/index.html",
    "https://www.landrover.in/range-rover-sport/index.html",
    "https://www.landrover.in/range-rover-velar/index.html",
    "https://www.landrover.in/range-rover-evoque/index.html",
    "https://www.landrover.in/defender/index.html",
    "https://www.landrover.in/discovery/index.html",
    "https://www.landrover.in/discovery-sport/index.html",
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{7,8})\b', body) if 5000000 <= int(n) <= 90000000))


SKIP = ["google","gtm","facebook","gstatic","fonts","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar",
        "bing","instagram","linkedin","x.com","twitter"]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(35000)

    apis = []
    def on_response(resp):
        u = resp.url
        low = u.lower()
        if any(s in low for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b):
                apis.append((u, b))
    page.on("response", on_response)

    for url in MODELS:
        apis.clear()
        name = url.split("/")[-2]
        log("\n" + "=" * 70)
        log(f"MODEL: {name}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=35000)
            st = resp.status if resp else "?"
            log(f"  [{st}] {url}")
            if st != 200:
                continue
            page.wait_for_timeout(5000)
            for _ in range(6):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)

            # price/configure/specs links
            hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
            plinks = sorted(set(h for h in hrefs if any(k in h.lower() for k in
                            ["price","configure","specification","spec","build","models-and-pricing","offers"])))
            if plinks:
                log(f"  price/config links:")
                for h in plinks[:6]:
                    log(f"    {h}")

            # API
            if apis:
                log(f"  price API ({len(apis)}):")
                seen = set()
                for u, b in apis:
                    base = u.split("?")[0]
                    if base in seen: continue
                    seen.add(base)
                    log(f"    {u[:100]}")
                    log(f"      prices: {real_prices(b)[:10]}")

            # ₹ prices
            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if ("₹" in l or "INR" in l or "Rs" in l) and re.search(r"\d{5,}", l)]
            if plines:
                log(f"  ₹ lines ({len(plines)}):")
                for l in plines[:8]:
                    log(f"    {l[:50]}")
            else:
                log(f"  (koi ₹ price nahi)")
        except Exception as e:
            log(f"  fail: {str(e)[:45]}")

    browser.close()

with open("landrover2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. landrover2.txt UPLOAD kar do.")
print("=" * 60)