"""
debug_citroen2.py — Citroen configurator API (model list + variants)
=====================================================================
MIL GAYA! Citroen ka clean API:
  https://configuratorapi.citroen.in/api/v1/model/all?lang_code=en-IN
  https://configuratorapi.citroen.in/api/v1/variants/all?model_id=X&lang_code=en-IN

Ye script dono API directly call karta hai (browser context me) — model list
(id+naam) + har model ke variants (naam+price+fuel) capture karta hai.

CHALAO:
    python debug_citroen2.py

Banega: citroen_models.json + citroen_variants.json + citroen2.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

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

    # warmup — configurator site khol ke session
    try:
        page.goto("https://www.citroen.in/models/c3.html", wait_until="domcontentloaded", timeout=50000)
        page.wait_for_timeout(4000)
    except Exception as e:
        log(f"warmup: {str(e)[:40]}")

    def fetch_json(url):
        try:
            return page.evaluate("""async (u) => {
                const r = await fetch(u, {headers:{'Content-Type':'application/json'}});
                return await r.text();
            }""", url)
        except Exception as e:
            return None

    # 1. model list
    log("=" * 70)
    log("MODEL LIST")
    log("=" * 70)
    ml_raw = fetch_json("https://configuratorapi.citroen.in/api/v1/model/all?lang_code=en-IN")
    model_ids = {}
    if ml_raw:
        with open("citroen_models.json", "w", encoding="utf-8") as f:
            f.write(ml_raw)
        try:
            data = json.loads(ml_raw)
            items = data.get("data") or data.get("models") or data
            if isinstance(items, dict):
                items = items.get("models") or list(items.values())
            log(f"  models: {len(items) if hasattr(items,'__len__') else '?'}")
            if isinstance(items, list):
                for m in items:
                    if isinstance(m, dict):
                        mid = m.get("id") or m.get("model_id")
                        nm = m.get("name") or m.get("model_name") or m.get("title")
                        log(f"    id={mid}  {nm}")
                        if mid and nm:
                            model_ids[mid] = nm
        except Exception as e:
            log(f"  parse err: {e}")
            log(f"  raw: {ml_raw[:400]}")

    # 2. har model ke variants
    log("\n" + "=" * 70)
    log("VARIANTS per model")
    log("=" * 70)
    all_variants = {}
    ids_to_try = list(model_ids.keys()) or [1, 2, 3, 4, 5]
    for mid in ids_to_try:
        url = f"https://configuratorapi.citroen.in/api/v1/variants/all?model_id={mid}&postcode=null&shown_at=web&lang_code=en-IN"
        raw = fetch_json(url)
        if not raw:
            continue
        all_variants[mid] = raw
        try:
            data = json.loads(raw)
            variants = data.get("data") or data.get("variants") or []
            if isinstance(variants, dict):
                variants = variants.get("variants") or list(variants.values())
            mname = model_ids.get(mid, f"model_{mid}")
            log(f"\n  {mname} (id={mid}): {len(variants) if hasattr(variants,'__len__') else '?'} variants")
            if isinstance(variants, list):
                for v in variants[:12]:
                    if isinstance(v, dict):
                        vn = v.get("name") or v.get("variant_name") or v.get("title") or ""
                        pr = v.get("price") or v.get("ex_showroom_price") or v.get("base_price") or ""
                        fu = v.get("fuel_type") or v.get("fuel") or v.get("engine") or ""
                        log(f"      {str(vn)[:32]:32} | Rs {pr} | {fu}")
                        # keys of first
                if variants and isinstance(variants[0], dict):
                    log(f"      (keys: {list(variants[0].keys())[:12]})")
        except Exception as e:
            log(f"    parse err (id={mid}): {e}")

    # saari variants ek file me
    with open("citroen_variants.json", "w", encoding="utf-8") as f:
        json.dump(all_variants, f)

    browser.close()

with open("citroen2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. citroen_models.json + citroen_variants.json + citroen2.txt UPLOAD karo.")
print("=" * 60)