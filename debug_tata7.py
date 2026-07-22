"""
debug_tata7.py — Diesel/CNG ka data kaise aata hai, ye pata karne ke liye
=========================================================================
Nexon page kholte hain, phir Diesel radio button click karte hain, aur
dekhte hain kaunsa naya API call hota hai (uska poora URL). Us URL me
fuel ka parameter hoga — usse har fuel ka data mil jayega.
"""
from playwright.sync_api import sync_playwright

URL = "https://cars.tatamotors.com/nexon/ice/price.html"
api_calls = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(response):
        if "getpricefilteredresult" in response.url:
            api_calls.append(response.url)
            print(f"  API call: {response.url}")

    page.on("response", on_response)

    print(f"Kholte hain: {URL}\n")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(600)
    page.wait_for_timeout(2000)

    print("\n--- Ab Diesel click karte hain ---")
    try:
        # radio button ya label — dono try
        for sel in ["text=Diesel", "label:has-text('Diesel')", "input[value='Diesel']"]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.click(timeout=4000)
                    print(f"  clicked via: {sel}")
                    break
            except Exception:
                continue
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"  Diesel click error: {e}")

    print("\n--- Ab Bi-fuel CNG click karte hain ---")
    try:
        for sel in ["text=Bi-fuel CNG", "text=CNG", "label:has-text('CNG')"]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.click(timeout=4000)
                    print(f"  clicked via: {sel}")
                    break
            except Exception:
                continue
        page.wait_for_timeout(3000)
    except Exception as e:
        print(f"  CNG click error: {e}")

    print(f"\n=== KUL {len(api_calls)} API calls hui ===")
    for i, u in enumerate(api_calls):
        print(f"  [{i}] {u}")

    # ab current page ka text bhi dekhte hain — Diesel/CNG variants dikh rahe?
    txt = page.inner_text("body")
    print("\n=== Abhi page pe jo variant cards hain (Price* wale) ===")
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if i+1 < len(lines) and lines[i+1] == "Price *":
            print("  ", repr(l))

    browser.close()
    print("\nDONE.")