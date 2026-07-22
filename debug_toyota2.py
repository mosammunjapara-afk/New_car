"""
debug_toyota2.py — Toyota pricelist + Glanza page ka structure dekho
=====================================================================
Do URL: /pricelist/ (saari cars) aur /showroom/glanza/ (ek car)
Dono ka text + API dekhte hain, variant/price kaise hain pata karte hain.
"""
from playwright.sync_api import sync_playwright
import re

URLS = [
    ("pricelist", "https://www.toyotabharat.com/pricelist/"),
    ("glanza", "https://www.toyotabharat.com/showroom/glanza/"),
]
apis = []

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
                if any(k in b.lower() for k in ["price","variant","grade","model"]):
                    apis.append((u, b[:150]))
            except Exception: pass

    page.on("response", on_response)

    for name, url in URLS:
        try:
            print(f"\n{'='*55}\n{name.upper()}: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(6000)
            for _ in range(8):
                page.mouse.wheel(0, 1000); page.wait_for_timeout(500)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            print(f"  page {len(txt)} chars")
            with open(f"toyota_{name}.txt", "w", encoding="utf-8") as f:
                f.write(txt)
            print(f"  Saved: toyota_{name}.txt")
            # price + variant jaisi lines
            prices = re.findall(r"(₹\s*[\d,\. ]{4,}|Rs\.?\s*[\d,\. ]{4,}|INR\s*[\d,\. ]{4,}|[\d,\.]+\s*[Ll]akh)", txt)
            print(f"  {len(prices)} price-jaisi lines. Pehli 15:")
            for pp in prices[:15]:
                print("    ", repr(pp.strip()))
        except Exception as e:
            print(f"  ✗ {str(e)[:55]}")

    print(f"\n=== {len(apis)} JSON API ===")
    seen=set()
    for u, prev in apis:
        b=u.split("?")[0]
        if b in seen: continue
        seen.add(b)
        print(f"  {u[:95]}")
        print(f"    {prev[:100]}")

    browser.close()
    print("\nDONE. toyota_pricelist.txt aur toyota_glanza.txt bhej do.")