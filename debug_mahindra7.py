"""
debug_mahindra7.py — modal-data.json seedha kholo (Mahindra ki asli data file!)
================================================================================
3D engine 'modal-data.json' se data laata hai. Wahi seedha kholte hain.
one3dui.js ka path: .../Visualize360/XUV700/assets/one3d/assets/XUV700/one3dui.js
To modal-data.json: .../Visualize360/XUV700/assets/one3d/assets/XUV700/modal-data.json
"""
from playwright.sync_api import sync_playwright
import json, re

# XUV700 ke liye — basefolder wahi jahan one3dui.js tha
CANDIDATES = [
    "https://auto.mahindra.com/on/demandware.static/-/Sites-amc-Library/en_IN/v1784047636845/Visualize360/XUV700/assets/one3d/assets/XUV700/modal-data.json",
    "https://auto.mahindra.com/on/demandware.static/-/Sites-amc-Library/en_IN/v1784047636845/Visualize360/XUV700/assets/one3d/assets/modal-data.json",
    "https://auto.mahindra.com/on/demandware.static/-/Sites-amc-Library/en_IN/v1784047636845/Visualize360/XUV700/assets/modal-data.json",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    found = None
    for url in CANDIDATES:
        try:
            print(f"\nTry: ...{url[-70:]}")
            page.goto(url, timeout=30000)
            body = page.inner_text("body")
            if body.strip().startswith(("{","[")) and len(body) > 100:
                data = json.loads(body)
                print(f"  ✓ MILA! JSON hai ({len(body)} chars)")
                found = (url, data)
                break
            else:
                print(f"  ✗ {body[:50]}")
        except Exception as e:
            print(f"  ✗ {str(e)[:50]}")

    if found:
        url, data = found
        with open("mahindra_modaldata.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved: mahindra_modaldata.json")
        print(f"\n=== Top-level keys ===")
        if isinstance(data, dict):
            print(" ", list(data.keys()))
            variants = data.get("variants", [])
            print(f"\n  {len(variants)} variants:")
            for v in variants[:20]:
                if isinstance(v, dict):
                    # variant naam + price wali keys dhoondho
                    name = v.get("variant_name") or v.get("name") or v.get("variantName") or v.get("label") or "?"
                    price = v.get("variant_price") or v.get("price") or v.get("ex_showroom") or "?"
                    print(f"    {name}  ->  {price}")
            if variants and isinstance(variants[0], dict):
                print(f"\n  Pehle variant ki keys: {list(variants[0].keys())}")
    else:
        print("\nModal-data URL nahi mila. Exact basefolder chahiye.")

    browser.close()
    print("\nDONE.")