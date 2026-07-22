"""
debug_toyota4.py — API page ke andar se pakdo (session chahiye, Tata jaisa)
===========================================================================
webapi.tfsin API seedha nahi khulta. Glanza page kholte hain, aur jo
'models/{id}/variants' call hota hai use pakadte hain. Saath me alag
model pages khol ke unke IDs + variants bhi pakadte hain.
"""
from playwright.sync_api import sync_playwright
import json

# kuch model pages (inke andar se API call hoga)
MODEL_PAGES = {
    "glanza": "https://www.toyotabharat.com/showroom/glanza/",
    "hyryder": "https://www.toyotabharat.com/showroom/urban-cruiser-hyryder/",
    "innova-hycross": "https://www.toyotabharat.com/showroom/innova-hycross/",
    "fortuner": "https://www.toyotabharat.com/showroom/fortuner/",
    "taisor": "https://www.toyotabharat.com/showroom/taisor/",
    "rumion": "https://www.toyotabharat.com/showroom/rumion/",
    "innova-crysta": "https://www.toyotabharat.com/showroom/innova-crysta/",
    "hilux": "https://www.toyotabharat.com/showroom/hilux/",
}

captured = {}  # model -> variants json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    current = {"name": None}

    def on_response(resp):
        if "/variants" in resp.url and "toyotabharat" in resp.url:
            try:
                data = resp.json()
                if current["name"]:
                    captured[current["name"]] = (resp.url, data)
            except Exception:
                pass

    page.on("response", on_response)

    for name, url in MODEL_PAGES.items():
        current["name"] = name
        try:
            print(f"\n{name}: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)
            for _ in range(6):
                page.mouse.wheel(0, 1000); page.wait_for_timeout(500)
            page.wait_for_timeout(2000)
            if name in captured:
                u, data = captured[name]
                variants = data.get("variants", [])
                print(f"  ✓ {len(variants)} variants (modelId in URL: {u.split('/models/')[1].split('/')[0] if '/models/' in u else '?'})")
                # ek variant ka price dikhao
                if variants:
                    v = variants[0]
                    pkeys = {k:val for k,val in v.items() if 'price' in k.lower()}
                    print(f"    keys: {list(v.keys())}")
                    print(f"    price keys: {pkeys}")
            else:
                print(f"  ✗ variants API nahi pakda")
        except Exception as e:
            print(f"  ✗ {str(e)[:50]}")

    # sab save karo
    if captured:
        out = {name: data for name,(u,data) in captured.items()}
        with open("toyota_all_variants.json","w",encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"\n✓ Saved: toyota_all_variants.json ({len(captured)} models)")

    browser.close()
    print("\nDONE. toyota_all_variants.json bhej do.")