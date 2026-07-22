"""
debug_mahindra.py — Mahindra ka price page structure + API dhoondhne ke liye
=============================================================================
Thar / XUV700 ka price page khol ke API + text dono check karta hai.
"""
from playwright.sync_api import sync_playwright
import re

URLS = [
    "https://auto.mahindra.com/suv/thar/price.html",
    "https://auto.mahindra.com/suv/xuv700",
    "https://www.mahindra.com/suv/thar",
    "https://auto.mahindra.com/suv/thar",
    "https://cars.mahindra.com/thar/price",
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
        if any(x in u for x in ["chat360","google","doubleclick","gtm","analytics","facebook"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price","variant","trim","exshowroom","showroom"]):
                    json_apis.append((u, body[:150]))
            except Exception:
                pass

    page.on("response", on_response)

    for url in URLS:
        try:
            print(f"\n=== Try: {url} ===")
            page.goto(url, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            prices = re.findall(r"(₹\s*[\d,\. ]{3,}|Rs\.?\s*[\d,\. ]{3,}|[\d,\.]+\s*[Ll]akh)", txt)
            print(f"  page {len(txt)} chars, {len(prices)} price-lines")
            if len(txt) > 1000 and len(prices) > 2:
                with open("mahindra_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                print("  ✓ Saved: mahindra_page_text.txt")
                for pp in prices[:12]:
                    print("    ", repr(pp.strip()))
                break
        except Exception as e:
            print(f"  ✗ {str(e)[:55]}")

    print(f"\n=== {len(json_apis)} JSON API (price/variant) ===")
    seen=set()
    for u, prev in json_apis:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  {u[:100]}")
        print(f"     {prev[:110]}")

    browser.close()
    print("\nDONE. mahindra_page_text.txt ya screenshot bhej do.")