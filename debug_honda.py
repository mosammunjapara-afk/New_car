"""
debug_honda.py — Honda ka price page structure + API dhoondhne ke liye
=======================================================================
City / Elevate ka price page khol ke API + text dono check karta hai.
"""
from playwright.sync_api import sync_playwright
import re

URLS = [
    "https://www.hondacarindia.com/city/price",
    "https://www.hondacarindia.com/elevate",
    "https://www.hondacarindia.com/city",
    "https://www.hondacarindia.com/amaze",
    "https://www.hondacarindia.com/price-list",
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
        if any(x in u for x in ["chat360","google","doubleclick","gtm","analytics","facebook","gstatic","fonts"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                b = resp.text()
                if any(k in b.lower() for k in ["price","variant","grade","model","trim"]):
                    json_apis.append((u, b[:150]))
            except Exception: pass

    page.on("response", on_response)

    for url in URLS:
        try:
            print(f"\n=== Try: {url} ===")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(6000)
            for _ in range(7):
                page.mouse.wheel(0, 1100); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            prices = re.findall(r"(₹\s*[\d,\. ]{4,}|Rs\.?\s*[\d,\. ]{4,}|[\d,\.]+\s*[Ll]akh)", txt)
            print(f"  page {len(txt)} chars, {len(prices)} price-lines")
            if len(txt) > 1000 and len(prices) > 2:
                with open("honda_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                print("  ✓ Saved: honda_page_text.txt")
                for pp in prices[:12]:
                    print("    ", repr(pp.strip()))
                # variant jaisi lines
                for line in txt.split("\n"):
                    l=line.strip()
                    if "|" in l and len(l)<50: print("   |", repr(l))
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
    print("\nDONE. honda_page_text.txt ya screenshot bhej do.")