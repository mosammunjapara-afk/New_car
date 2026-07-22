"""
debug_citroen3.py — Citroen API ko PAGE-LOAD pe capture karo (direct fetch 401)
===============================================================================
Direct fetch 401 (auth chahiye). Par page-load pe ye API khud fire hoti hai
(debug1 me data aaya tha). Toh page khol ke un responses ko capture karte hain.

Har model page khol ke variants/all + model/all response capture.

CHALAO:
    python debug_citroen3.py

Banega: citroen_v2.json (saari variants) + citroen3.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

MODEL_PAGES = [
    "https://www.citroen.in/models/basalt.html",
    "https://www.citroen.in/models/c3.html",
    "https://www.citroen.in/models/aircross.html",
    "https://www.citroen.in/models/new-e-c3.html",
    "https://www.citroen.in/models/c5-aircross.html",
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

    model_all = {"body": None}
    variants_by_url = {}
    def on_response(resp):
        u = resp.url
        if "configuratorapi.citroen.in/api/v1/model/all" in u:
            try:
                model_all["body"] = resp.text()
            except Exception:
                pass
        elif "configuratorapi.citroen.in/api/v1/variants/all" in u:
            try:
                variants_by_url[u] = resp.text()
            except Exception:
                pass
    page.on("response", on_response)

    for url in MODEL_PAGES:
        log(f"\nPAGE: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=50000)
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            page.wait_for_timeout(2000)
        except Exception as e:
            log(f"  fail: {str(e)[:40]}")

    # model/all
    log("\n" + "=" * 70)
    log("MODEL LIST")
    log("=" * 70)
    if model_all["body"]:
        try:
            data = json.loads(model_all["body"])
            items = data.get("data") if isinstance(data, dict) else data
            if isinstance(items, list):
                log(f"  models: {len(items)}")
                for m in items:
                    log(f"    id={m.get('id')}  {m.get('name')}  (keys: {list(m.keys())[:8]})")
        except Exception as e:
            log(f"  parse err: {e} | raw: {model_all['body'][:200]}")

    # variants
    log("\n" + "=" * 70)
    log("VARIANTS")
    log("=" * 70)
    saved = {}
    for u, body in variants_by_url.items():
        mid = re.search(r'model_id=(\d+)', u)
        mid = mid.group(1) if mid else "?"
        saved[mid] = body
        try:
            data = json.loads(body)
            variants = data.get("data") if isinstance(data, dict) else data
            log(f"\n  model_id={mid}: {len(variants) if hasattr(variants,'__len__') else '?'} variants")
            if isinstance(variants, list):
                if variants and isinstance(variants[0], dict):
                    log(f"    keys: {list(variants[0].keys())}")
                for v in variants[:12]:
                    if isinstance(v, dict):
                        vn = v.get("name") or v.get("variant_name") or v.get("version_name") or ""
                        pr = v.get("price") or v.get("ex_showroom_price") or v.get("base_price") or v.get("starting_price") or ""
                        fu = v.get("fuel_type") or v.get("fuel") or v.get("energy") or ""
                        log(f"      {str(vn)[:32]:32} | Rs {pr} | {fu}")
        except Exception as e:
            log(f"  parse err (id={mid}): {e}")

    with open("citroen_v2.json", "w", encoding="utf-8") as f:
        json.dump({"model_all": model_all["body"], "variants": saved}, f)

    browser.close()

with open("citroen3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. citroen_v2.json + citroen3.txt UPLOAD karo.")
print("=" * 60)