"""
debug_tata5.py — Tata ke JSON API se saare variants + prices nikaalo
=====================================================================
Mil gaya API: /price.getpricefilteredresult.json
Ye saare variants ek saath deta hai. Isko seedha padh ke prices nikaalte hain.
"""
from playwright.sync_api import sync_playwright
import json

# Nexon ka API (aur models ke liye "nexon" ki jagah dusra model)
API_URL = "https://cars.tatamotors.com/nexon/ice/price.getpricefilteredresult.json"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print(f"API kholte hain: {API_URL}")
    # API ko seedha browser me kholo (JSON milega)
    resp = page.goto(API_URL, timeout=60000)
    body = page.inner_text("body")

    # save karo
    with open("tata_nexon_api.json", "w", encoding="utf-8") as f:
        f.write(body)
    print(f"Saved: tata_nexon_api.json ({len(body)} chars)")

    # parse karke variants dikhao
    try:
        data = json.loads(body)
        variants = data.get("results", {}).get("variantPriceFeatures", [])
        print(f"\n=== {len(variants)} VARIANTS mile ===\n")
        for v in variants:
            label = v.get("variantLabel", "?")
            # price dhoondho — alag keys me ho sakta hai
            price = (v.get("price") or v.get("exShowroomPrice") or
                     v.get("variantPrice") or v.get("displayPrice"))
            # kabhi kabhi price nested hota hai
            if not price:
                for k, val in v.items():
                    if "price" in k.lower() and isinstance(val, (int, str)):
                        price = val
                        break
            print(f"  {label:40s} | price={price}")

        # ek variant ka poora structure dikhao (taaki price ki sahi key pata chale)
        if variants:
            print("\n=== Pehle variant ka poora structure (keys) ===")
            print("  keys:", list(variants[0].keys()))
            print("\n  Poora pehla variant:")
            print(json.dumps(variants[0], indent=2)[:800])
    except Exception as e:
        print("Parse error:", e)
        print("Body preview:", body[:300])

    browser.close()
    print("\nDONE. Agar prices dikhi to Tata ban jayega!")