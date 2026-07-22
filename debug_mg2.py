"""
debug_mg2.py — MG variants API ki POORI response (structure ke liye)
====================================================================
MIL GAYA! MG variant API:
  https://eeysubngbk.execute-api.ap-south-1.amazonaws.com/prod/api/variants
  (saare models ke variants + exact prices — ek call me)

Ye script us API ki poori response capture karta hai — model + variant + price
+ fuel structure dekhne ke liye.

CHALAO:
    python debug_mg2.py

Banega: mg_variants.json + mg2.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

# ek MG page jahan variants API fire hoti hai
PAGE = "https://www.mgmotor.co.in/service/astor-my-mg-shield"

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

    captured = {"body": None, "url": None}
    def on_response(resp):
        if "/api/variants" in resp.url:
            try:
                captured["body"] = resp.text()
                captured["url"] = resp.url
            except Exception:
                pass
    page.on("response", on_response)

    log(f"Kholte hain: {PAGE}")
    try:
        page.goto(PAGE, wait_until="domcontentloaded", timeout=50000)
        page.wait_for_timeout(6000)
        for _ in range(6):
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(600)
        page.wait_for_timeout(3000)
    except Exception as e:
        log(f"  page fail: {str(e)[:50]}")

    if captured["body"]:
        with open("mg_variants.json", "w", encoding="utf-8") as jf:
            jf.write(captured["body"])
        log(f"\nsaved: mg_variants.json ({len(captured['body'])} chars)")
        log(f"URL: {captured['url']}")
        try:
            data = json.loads(captured["body"])
            log(f"\ntop type: {type(data).__name__}")
            if isinstance(data, dict):
                log(f"top keys: {list(data.keys())}")
                # data.data ya data.variants
                items = data.get("data") or data.get("variants") or data.get("body")
                if isinstance(items, str):
                    items = json.loads(items)
            else:
                items = data
            log(f"items type: {type(items).__name__}")
            if isinstance(items, list):
                log(f"total items: {len(items)}")
                if items:
                    log(f"\nek item ke keys: {list(items[0].keys())}")
                    log(f"\nek item poora:")
                    log(json.dumps(items[0], indent=2, ensure_ascii=False)[:800])
                    # model + variant + price fields
                    log(f"\n--- saare items (model | variant | price) ---")
                    seen_models = {}
                    for it in items:
                        m = it.get("model") or it.get("modelName") or it.get("carModel") or ""
                        v = it.get("variant") or it.get("variantName") or it.get("name") or ""
                        pr = it.get("price") or it.get("exShowroomPrice") or it.get("variantPrice") or ""
                        fu = it.get("fuel") or it.get("fuelType") or ""
                        seen_models.setdefault(m, 0)
                        seen_models[m] += 1
                        if seen_models[m] <= 4:
                            log(f"    {m[:15]:15} | {str(v)[:28]:28} | {pr} | {fu}")
                    log(f"\n  models found: {dict(seen_models)}")
        except Exception as e:
            log(f"  parse err: {str(e)[:60]}")
            log(f"  raw start: {captured['body'][:400]}")
    else:
        log("\n  variants API capture nahi hui")

    browser.close()

with open("mg2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. mg_variants.json + mg2.txt UPLOAD karo.")
print("=" * 60)