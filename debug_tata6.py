"""
debug_tata6.py — Tata API response ko page ke andar se pakdo
=============================================================
API seedha nahi khulta (session chahiye). Isliye page kholte hain aur jab
page KHUD 'getpricefilteredresult.json' call kare, uska response pakad lete hain.
Ye pakka kaam karta hai.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"
captured_json = {"data": None}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(response):
        if "getpricefilteredresult" in response.url:
            try:
                captured_json["data"] = response.json()
                print(f"  ✓ Pakda: {response.url[:70]}")
            except Exception as e:
                print(f"  response mila par parse nahi hua: {e}")

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    # scroll taaki price section load ho aur API call ho
    for _ in range(5):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(700)
    page.wait_for_timeout(3000)

    data = captured_json["data"]
    if not data:
        print("\n✗ API response nahi pakda. Shayad naam thoda alag hai.")
        browser.close()
    else:
        with open("tata_nexon_api.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved: tata_nexon_api.json")

        variants = data.get("results", {}).get("variantPriceFeatures", [])
        print(f"\n=== {len(variants)} VARIANTS mile ===\n")
        for v in variants:
            label = v.get("variantLabel", "?")
            # price key dhoondho
            price = None
            for k, val in v.items():
                if "price" in k.lower() and isinstance(val, (int, float)):
                    price = val; break
                if "price" in k.lower() and isinstance(val, str) and val.replace(",","").replace(".","").isdigit():
                    price = val; break
            print(f"  {label:40s} | {price}")

        if variants:
            print("\n=== Pehle variant ki saari keys ===")
            print(" ", list(variants[0].keys()))
        browser.close()
    print("\nDONE.")