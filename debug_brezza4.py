"""
debug_brezza4.py — Brezza ka poora HTML + variant API dhoondo
=============================================================
Brezza ke variant cards render nahi ho rahe (Swift me hote hain). Jo 9 price
dikhe wo Arena EMI-selector list thi (3.49L se - saari cars), Brezza ke nahi.

Ye script:
  1. Brezza page ka poora rendered HTML save karta hai (main khud parse karunga)
  2. Koi variant-price JSON API to nahi, wo capture karta hai
  3. "Brezza" naam ke saath price dhoondta hai

CHALAO:
    python debug_brezza4.py

Banega:
  - brezza_page.html  (ZAROORI - upload karo)
  - brezza4.txt
"""

from playwright.sync_api import sync_playwright
import re

URL = "https://www.marutisuzuki.com/arena/brezza/price"

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

    apis = []
    def on_response(resp):
        u = resp.url
        if any(x in u.lower() for x in ["google","gtm","facebook","font",".css",".png",
                                        ".jpg",".svg",".woff","analytics","clarity"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if re.search(r'\d{5,7}', b) and any(k in b.lower() for k in
                    ["variant","price","brezza","model","grade"]):
                apis.append((u, b))
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    try:
        page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(4000)
    # khoob scroll — variant cards trigger
    for _ in range(15):
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(500)
    page.wait_for_timeout(3000)

    # poora HTML save
    html = page.content()
    with open("brezza_page.html", "w", encoding="utf-8") as hf:
        hf.write(html)
    log(f"HTML saved: brezza_page.html ({len(html)} chars)")

    # variant price API
    log(f"\n=== variant/price JSON APIs: {len(apis)} ===")
    seen = set()
    for u, b in apis:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        prices = sorted(set(int(x) for x in re.findall(r'\b(\d{6,7})\b', b) if 500000 <= int(x) <= 2000000))
        log(f"  {u[:100]}")
        log(f"    Brezza-range prices: {prices[:15]}")
        log(f"    sample: {b[:250].replace(chr(10),' ')}")

    # HTML me "Brezza" ke saath variant naam (LXI, VXI, ZXI, ZXI+)
    log("\n=== HTML me Brezza variant naam ===")
    for trim in ["LXI", "VXI", "ZXI", "ZXI+", "Lxi", "Vxi", "Zxi"]:
        c = html.count(trim)
        if c:
            log(f"  {trim}: {c}x")

    browser.close()

with open("brezza4.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. Ye upload karo:")
print("  - brezza_page.html (ZAROORI)")
print("  - brezza4.txt")
print("=" * 60)