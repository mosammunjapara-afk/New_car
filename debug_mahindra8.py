"""
debug_mahindra8.py — "BUILD & PRICE" click karke price API pakdo
=================================================================
Config page pe "BUILD & PRICE" button dabane pe price API call hota hai
(unique_code -> price). Us call ko pakadte hain. Aur unique_code ke saath
seedha price API guess bhi karte hain.
"""
from playwright.sync_api import sync_playwright
import re, json

URL = "https://auto.mahindra.com/XUV700.html"
api_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","evergage","qualtrics","google-analytics","gstatic","fonts",".png",".jpg",".css",".woff",".mp4",".svg",".js"]):
            return
        try:
            body = resp.text()
            low = body.lower()
            # price ya bade number (5-8 digit)
            if ("price" in low or "exshowroom" in low or re.search(r'\d{6,8}', body)) and len(body) < 50000:
                api_hits.append((resp.request.method, u, body[:400]))
        except Exception:
            pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)
    print("  Config load hone dete hain (40 sec)...")
    for i in range(14):
        page.wait_for_timeout(3000)
        try:
            page.mouse.move(600, 400); page.mouse.wheel(0, 200)
        except Exception: pass

    # "BUILD & PRICE" button click
    print("\n  'BUILD & PRICE' button dhoondh ke click...")
    clicked = False
    for sel in ["text=BUILD & PRICE", "text=Build & Price", "[onclick*='build_price']",
                ".one3d-build-n-price-btn", "text=Build and Price"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(timeout=5000)
                clicked = True
                print(f"  ✓ clicked: {sel}")
                page.wait_for_timeout(6000)
                break
        except Exception as e:
            pass
    if not clicked:
        print("  ✗ button nahi mila")

    page.wait_for_timeout(3000)

    print(f"\n=== {len(api_hits)} price-jaisi calls ===")
    seen=set()
    for method, u, prev in api_hits:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  [{method}] {u[:100]}")
        print(f"  preview: {prev[:250]}")

    # page pe ab ₹ price dikha?
    txt = page.inner_text("body")
    print("\n=== Page pe ₹-price ===")
    for line in txt.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            print("  ", repr(line.strip()[:50]))

    browser.close()
    print("\nDONE.")