"""
debug_kia2.py — Carnival, EV9, EV6, Carens ke variant naam + price dekhna
==========================================================================
In 4 models ke page ka text nikaalta hai, taaki pata chale variant naam
kaise hain (Limousine, GT-Line, etc.) aur price kaise likhi hai.
"""
from playwright.sync_api import sync_playwright
import re

MODELS = ["carnival", "ev9", "ev6", "carens"]
BASE = "https://www.kia.com/in/our-vehicles"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    for slug in MODELS:
        try:
            url = f"{BASE}/{slug}.html"
            print(f"\n{'='*50}\n{slug.upper()}: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            for _ in range(8):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(500)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")

            # "Trims Available" ya price ke aas-paas ka text dikhao
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            # har ₹ line aur uske upar ki line (variant naam) dikhao
            print("  --- Price ke aas-paas (variant + price) ---")
            for i, l in enumerate(lines):
                if re.search(r"₹\s*[\d,]{5,}", l):
                    # upar ki 2 lines (variant naam) + ye price line
                    prev = lines[i-1] if i > 0 else ""
                    prev2 = lines[i-2] if i > 1 else ""
                    print(f"    [{prev2[:25]}] [{prev[:25]}] -> {l[:40]}")
            # "Trims Available" line
            for l in lines:
                if "trim" in l.lower() and "available" in l.lower():
                    print(f"  >> {l}")
        except Exception as e:
            print(f"  ✗ {str(e)[:60]}")

    browser.close()
    print("\n\nDONE. Screenshot bhej do.")