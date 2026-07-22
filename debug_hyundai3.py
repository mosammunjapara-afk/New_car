"""
debug_hyundai3.py — Creta page ke background API calls capture + models price dekho
====================================================================================
2 cheezein:
  1. hyundai_models.json me price/exPrice kya hai, dikhao
  2. Creta ka price page kholo aur dekho kaunse API call hote hain (variant price ke liye)
"""
from playwright.sync_api import sync_playwright
import json

# 1. models file padho (agar hai)
try:
    models = json.load(open("hyundai_models.json", encoding="utf-8"))
    print("=== Models me price fields ===")
    for m in models[:5]:
        print(f"  {m.get('description'):25s} price={m.get('price')} exPrice={m.get('exPrice')}")
    print(f"\n  Pehle model ka poora data:")
    print(json.dumps(models[0], indent=2)[:600])
except Exception as e:
    print("models file nahi mili:", e)

# 2. Creta page ke API calls dekho
api_hits = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if "api.hyundai" in u or "price" in u.lower() or "variant" in u.lower():
            ct = resp.headers.get("content-type", "")
            if "json" in ct:
                try:
                    body = resp.text()
                    api_hits.append((u, body[:120]))
                except Exception:
                    pass

    page.on("response", on_response)

    print("\n\n=== Creta price page kholte hain, API calls dekhte hain ===")
    for url in ["https://www.hyundai.com/in/en/vehicles/creta/price",
                "https://www.hyundai.com/in/en/find-a-car/creta/creta/price"]:
        try:
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(5000)
            for _ in range(5):
                page.mouse.wheel(0, 1000); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            if api_hits:
                break
        except Exception as e:
            print(f"  {url[-40:]}: {str(e)[:40]}")

    print(f"\n=== {len(api_hits)} API calls (price/variant wale) ===")
    seen = set()
    for u, prev in api_hits:
        base = u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  {u[:100]}")
        print(f"     {prev}")

    browser.close()
    print("\nDONE.")