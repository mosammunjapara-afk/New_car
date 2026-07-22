"""
debug_hyundai2.py — Hyundai ke JSON API se models + variants + prices
======================================================================
Mila: https://api.hyundai.co.in/service/price/getModels
Ye models deta hai. Har model ke variants/price ke liye related API
dhoondte hain (getVariants / getVariantPrice jaisa).
"""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. getModels API seedha kholo
    print("=== getModels ===")
    try:
        page.goto("https://api.hyundai.co.in/service/price/getModels?loc=IN&lan=en",
                  timeout=40000)
        body = page.inner_text("body")
        models = json.loads(body)
        print(f"  {len(models)} models mile:")
        for m in models[:40]:
            print(f"    id={m.get('id')}  code={m.get('code')}  {m.get('description')}")
        # save
        with open("hyundai_models.json", "w", encoding="utf-8") as f:
            json.dump(models, f, indent=2)
        print("  Saved: hyundai_models.json")

        # ek model ka poora structure
        if models:
            print("\n  Pehle model ki keys:", list(models[0].keys()))
    except Exception as e:
        print(f"  error: {e}")
        models = []

    # 2. Ab ek model (jaise Creta) ke variants/price ke API try karo
    #    Hyundai ke common endpoints
    print("\n=== Variant/Price API try (Creta) ===")
    # pehle ek model ka code/id lo
    test_code = None
    for m in models:
        if "creta" in str(m.get("description","")).lower():
            test_code = m.get("code")
            test_id = m.get("id")
            print(f"  Creta: code={test_code}, id={test_id}")
            break
    if not test_code and models:
        test_code = models[0].get("code")
        test_id = models[0].get("id")

    candidates = [
        f"https://api.hyundai.co.in/service/price/getVariants?loc=IN&lan=en&modelCode={test_code}",
        f"https://api.hyundai.co.in/service/price/getVariant?loc=IN&lan=en&modelCode={test_code}",
        f"https://api.hyundai.co.in/service/price/getModelVariants?loc=IN&lan=en&modelCode={test_code}",
        f"https://api.hyundai.co.in/service/price/getPrice?loc=IN&lan=en&modelCode={test_code}",
    ]
    for c in candidates:
        try:
            page.goto(c, timeout=30000)
            b = page.inner_text("body")
            if b.strip().startswith(("[","{")) and len(b) > 50:
                print(f"  ✓ {c[-60:]}")
                print(f"     preview: {b[:200]}")
                with open("hyundai_variants.json", "w", encoding="utf-8") as f:
                    f.write(b)
                print("     Saved: hyundai_variants.json")
                break
            else:
                print(f"  ✗ {c[-50:]} -> {b[:40]}")
        except Exception as e:
            print(f"  ✗ error: {str(e)[:40]}")

    browser.close()
    print("\nDONE. 'hyundai_models.json' aur 'hyundai_variants.json' (agar bani) bhej do.")