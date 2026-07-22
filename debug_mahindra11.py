"""
debug_mahindra11.py — Thar/naye models ka data source dhoondo
==============================================================
Ye models modal-data.json use nahi karte. Inka "variants & pricing"
alag se aata hai. Saare API calls + Product-ShowQuickView pattern dekhte hain.
"""
from playwright.sync_api import sync_playwright
import re, json

URL = "https://auto.mahindra.com/suv/thar/THRN.html"
api_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","evergage","qualtrics","google","gstatic","fonts",".png",".jpg",".css",".woff",".mp4",".svg"]):
            return
        try:
            body = resp.text()
            low = body.lower()
            # variant/price data + Product API
            if ("product-showquickview" in u.lower() or "product-" in u.lower()
                    or '"price"' in low or "exshowroom" in low
                    or (re.search(r'\d{6,8}', body) and ("variant" in low or "pid" in low))):
                if len(body) < 60000:
                    api_hits.append((resp.request.method, u, body[:300]))
        except Exception:
            pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)
    print("  Load + variants-pricing tak scroll (50 sec)...")
    for i in range(16):
        page.wait_for_timeout(3000)
        page.mouse.wheel(0, 700)

    # "Variants & Prices" ya "Show full range" click try
    for label in ["Variants & Prices", "Variants &", "Show full range", "VARIANTS & PRICING"]:
        try:
            el = page.get_by_text(label, exact=False).first
            if el.count() > 0:
                el.click(timeout=3000)
                page.wait_for_timeout(3000)
                print(f"  clicked: {label}")
                break
        except Exception:
            pass
    page.wait_for_timeout(3000)

    print(f"\n=== {len(api_hits)} data/API calls ===")
    seen=set()
    for method, u, prev in api_hits:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  [{method}] {u[:110]}")
        print(f"  {prev[:180]}")

    # page text me variant + price
    txt = page.inner_text("body")
    print("\n=== Page pe variant cards / ₹ ===")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if "₹" in l and re.search(r"\d", l):
            prev = lines[i-1] if i>0 else ""
            print(f"  [{prev[:25]}] {l[:35]}")

    browser.close()
    print("\nDONE.")