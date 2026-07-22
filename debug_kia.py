"""
debug_kia.py — Kia ka price page structure + API dhoondhne ke liye
==================================================================
Seltos ka price page khol ke: (1) network me JSON API dhoondta hai,
(2) page ka text nikaalta hai. Kia aksar Hyundai jaisa API deta hai.
"""
from playwright.sync_api import sync_playwright
import re, json

URLS = [
    "https://www.kia.com/in/buy/price-list.html",
    "https://www.kia.com/in/our-vehicles/seltos/price.html",
    "https://www.kia.com/in/our-vehicles/seltos.html",
    "https://www.kia.com/in/buy/build-price.html",
]

json_apis = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","google","doubleclick","cloudflare","gtm","analytics"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price", "variant", "trim", "grade", "showroom"]):
                    json_apis.append((u, body[:150]))
            except Exception:
                pass

    page.on("response", on_response)

    working = None
    for url in URLS:
        try:
            print(f"\n=== Try: {url} ===")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            prices = re.findall(r"(₹\s*[\d,\. ]{3,}|Rs\.?\s*[\d,\. ]{3,}|[\d,\.]+\s*[Ll]akh)", txt)
            print(f"  page {len(txt)} chars, {len(prices)} price-lines")
            if len(txt) > 1000 and len(prices) > 2 and not working:
                working = url
                with open("kia_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                print("  ✓ Saved: kia_page_text.txt")
                print("  Pehli 12 price-lines:")
                for pp in prices[:12]:
                    print("    ", repr(pp.strip()))
        except Exception as e:
            print(f"  ✗ {str(e)[:60]}")

    print(f"\n=== {len(json_apis)} JSON API mile (price/variant wale) ===")
    seen = set()
    for u, prev in json_apis:
        base = u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  {u[:100]}")
        print(f"     {prev[:110]}")

    browser.close()
    print("\nDONE. 'kia_page_text.txt' (agar bani) ya screenshot bhej do.")