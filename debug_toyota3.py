"""
debug_toyota3.py — Toyota ke JSON API se saare models + variants + prices
==========================================================================
Mila: webapi.tfsin.toyotabharat.com/1.0/api/cities/null/models/{id}/variants
Pehle models list ka API dhoondte hain, phir har model ke variants.
"""
from playwright.sync_api import sync_playwright
import json

API = "https://webapi.tfsin.toyotabharat.com/1.0/api"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. models list API try karo
    print("=== Models list API try ===")
    for url in [f"{API}/cities/null/models", f"{API}/models", f"{API}/cities/null/models/all"]:
        try:
            page.goto(url, timeout=25000)
            b = page.inner_text("body").strip()
            if b.startswith(("{","[")) and len(b) > 50:
                print(f"  ✓ {url}")
                data = json.loads(b)
                # models dikhao
                models = data if isinstance(data, list) else data.get("models", data.get("data", []))
                print(f"     {len(models)} models" if isinstance(models, list) else f"     keys: {list(data.keys())[:8]}")
                if isinstance(models, list):
                    for m in models[:20]:
                        if isinstance(m, dict):
                            print(f"       id={m.get('id') or m.get('modelId')}  {m.get('name') or m.get('modelName')}")
                    with open("toyota_models.json","w",encoding="utf-8") as f: json.dump(data,f,indent=2)
                    print("     Saved: toyota_models.json")
                break
            else:
                print(f"  ✗ {url[-40:]}: {b[:30]}")
        except Exception as e:
            print(f"  ✗ {url[-40:]}: {str(e)[:30]}")

    # 2. Glanza (id=18) ke variants — price key dekhne ke liye
    print("\n=== Glanza (modelId=18) variants ===")
    try:
        page.goto(f"{API}/cities/null/models/18/variants", timeout=25000)
        b = page.inner_text("body")
        data = json.loads(b)
        with open("toyota_variants.json","w",encoding="utf-8") as f: json.dump(data,f,indent=2)
        print("  Saved: toyota_variants.json")
        variants = data.get("variants", data if isinstance(data,list) else [])
        print(f"  {len(variants)} variants:")
        for v in variants[:15]:
            # price key dhoondho
            price = None
            for k,val in v.items():
                if "price" in k.lower() and isinstance(val,(int,float,str)):
                    price = f"{k}={val}"; break
            print(f"    {v.get('name','?'):20s} {price}")
        if variants:
            print(f"\n  Pehle variant ki keys: {list(variants[0].keys())}")
    except Exception as e:
        print(f"  ✗ {str(e)[:50]}")

    browser.close()
    print("\nDONE. toyota_models.json aur toyota_variants.json bhej do.")