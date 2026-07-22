"""
debug_jeep2.py — Jeep one3d variants API ki poori response
===========================================================
Jeep bhi Citroen jaisa one3d API use karta hai:
  https://prod-jeep-api.one3d.in/api/v1/variants/all  (visualizer page pe fire)

Ye script har Jeep visualizer page khol ke variants/all response capture karta
hai — variant naam + price + fuel structure ke liye.

CHALAO:
    python debug_jeep2.py

Banega: jeep_variants.json + jeep2.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

VISUALIZER_PAGES = [
    ("Compass", "https://www.jeep-india.com/new-compass/visualizer.html"),
    ("Meridian", "https://www.jeep-india.com/new-jeep-meridian/visualizer.html"),
    ("Wrangler", "https://www.jeep-india.com/wrangler-jl/visualizer.html"),
    ("Grand Cherokee", "https://www.jeep-india.com/new-grand-cherokee/visualizer.html"),
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    captured = {}  # model -> variants/all response
    current = {"model": None}
    def on_response(resp):
        u = resp.url
        if "one3d.in/api/v1/variants/all" in u:
            try:
                captured[current["model"]] = resp.text()
            except Exception:
                pass
    page.on("response", on_response)

    for model, url in VISUALIZER_PAGES:
        current["model"] = model
        log(f"\nPAGE: {model} → {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=50000)
            page.wait_for_timeout(7000)
            for _ in range(6):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(3000)
            log(f"  captured: {'YES' if captured.get(model) else 'no'}")
        except Exception as e:
            log(f"  fail: {str(e)[:40]}")

    # parse
    log("\n" + "=" * 70)
    log("VARIANTS")
    log("=" * 70)
    for model, body in captured.items():
        try:
            data = json.loads(body)
            r = data.get("response", data)
            mname = r.get("model_name", model)
            variants = r.get("variants", [])
            log(f"\n  {mname}: {len(variants)} variants")
            if variants and isinstance(variants[0], dict):
                log(f"    keys: {list(variants[0].keys())}")
            for v in variants[:15]:
                if isinstance(v, dict):
                    vn = v.get("variant_name", "")
                    vd = v.get("variant_desc", "")
                    pr = v.get("price", "")
                    log(f"      {str(vn)[:26]:26} | Rs {pr} | {vd[:35]}")
        except Exception as e:
            log(f"  {model} parse err: {e} | raw: {body[:150]}")

    with open("jeep_variants.json", "w", encoding="utf-8") as f:
        json.dump(captured, f)

    browser.close()

with open("jeep2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. jeep_variants.json + jeep2.txt UPLOAD karo.")
print("=" * 60)