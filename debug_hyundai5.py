"""
debug_hyundai5.py — Creta page (find-a-car) ke variant-price API pakadna
=========================================================================
URL: hyundai.com/in/en/find-a-car/creta
Is page pe jo API calls hote hain (price/variant wale), sabko capture karte hain.
Jaise Tata me getpricefilteredresult pakda tha, waise Hyundai ka variant API pakdenge.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://www.hyundai.com/in/en/find-a-car/creta"
api_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        # chatbot (chat360) ko ignore karo
        if "chat360" in u:
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct and ("hyundai" in u or "price" in u.lower() or "variant" in u.lower()):
            try:
                body = resp.text()
                # sirf wo jisme price/variant jaisa data ho
                if any(k in body.lower() for k in ["price", "variant", "grade", "exshowroom", "exprice"]):
                    api_hits.append((u, body))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)  # page ko settle hone do
    # scroll + variants section tak jao
    for _ in range(8):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(700)
    page.wait_for_timeout(3000)

    # "Price" ya "Variant" tab/button pe click karne ki koshish
    for label in ["Price", "Variants", "All Variants", "View Price", "Explore Price"]:
        try:
            el = page.get_by_text(label, exact=False).first
            if el.count() > 0:
                el.click(timeout=3000)
                page.wait_for_timeout(3000)
                print(f"  '{label}' click hua")
                break
        except Exception:
            pass
    page.wait_for_timeout(2000)

    print(f"\n=== {len(api_hits)} API calls (price/variant wale) ===")
    seen = set()
    saved = False
    for u, body in api_hits:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        print(f"\n  URL: {u[:110]}")
        print(f"  preview: {body[:200]}")
        # sabse bada/relevant save karo
        if not saved and len(body) > 200 and ("variant" in body.lower() or "grade" in body.lower() or "exprice" in body.lower()):
            with open("hyundai_variants.json", "w", encoding="utf-8") as f:
                f.write(body)
            print("  ^^ Saved: hyundai_variants.json")
            saved = True

    browser.close()
    print("\nDONE. 'hyundai_variants.json' (agar bani) ya screenshot bhej do.")