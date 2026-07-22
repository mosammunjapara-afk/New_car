"""
debug_mahindra9.py — price file/API dhoondo (modal-data.json ke aas-paas + unique_code)
=========================================================================================
base folder: .../Visualize360/XUV700/XUV700/
modal-data.json wahin tha. Price bhi wahin kisi file me ho sakti hai.
Aur unique_code (X700MM93416118195) ko price API pe try karte hain.
"""
from playwright.sync_api import sync_playwright
import json

BASE = "https://auto.mahindra.com/on/demandware.static/-/Sites-amc-Library/en_IN/v1784047636845/Visualize360/XUV700/assets/one3d/assets/XUV700"

# price file candidates (modal-data.json ke saath)
FILE_CANDIDATES = [
    f"{BASE}/price-data.json",
    f"{BASE}/price.json",
    f"{BASE}/pricing.json",
    f"{BASE}/variant-price.json",
    f"{BASE}/prices.json",
    f"{BASE}/modal-price.json",
    f"{BASE}/price-modal.json",
]

# Mahindra pricing API candidates (unique_code se)
UCODE = "X700MM93416118195"
API_CANDIDATES = [
    f"https://auto.mahindra.com/on/demandware.store/Sites-amc-Site/en_IN/Product-Variation?pid={UCODE}",
    f"https://auto.mahindra.com/on/demandware.store/Sites-amc-Site/en_IN/Product-GetPrice?pid={UCODE}",
    f"https://auto.mahindra.com/api/price/{UCODE}",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    print("=== Price FILE candidates ===")
    for url in FILE_CANDIDATES:
        try:
            page.goto(url, timeout=20000)
            b = page.inner_text("body").strip()
            if b.startswith(("{","[")) and len(b) > 50:
                print(f"  ✓✓ MILA: ...{url[-40:]} ({len(b)} chars)")
                print(f"     {b[:200]}")
                with open("mahindra_price.json","w",encoding="utf-8") as f: f.write(b)
                print("     Saved: mahindra_price.json")
            else:
                print(f"  ✗ ...{url[-40:]}: {b[:30]}")
        except Exception as e:
            print(f"  ✗ ...{url[-40:]}: {str(e)[:30]}")

    print("\n=== Price API candidates (unique_code se) ===")
    for url in API_CANDIDATES:
        try:
            page.goto(url, timeout=20000)
            b = page.inner_text("body").strip()
            if b.startswith(("{","[")) and len(b) > 30:
                print(f"  ✓✓ MILA: ...{url[-50:]}")
                print(f"     {b[:250]}")
            else:
                print(f"  ✗ ...{url[-45:]}: {b[:30]}")
        except Exception as e:
            print(f"  ✗ ...{url[-45:]}: {str(e)[:30]}")

    browser.close()
    print("\nDONE.")