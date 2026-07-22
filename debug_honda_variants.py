"""
debug_honda_variants.py — Honda ke variant/fuel/transmission COMBOS pakdo
==========================================================================
MIL GAYA: POST /api/getCarPrice
  body: {"city":"Delhi","fuelType":"Petrol","transmission":"MT (Manual)","variant":"SV"}
  resp: {"code":200,"data":[{"P_Price":"1159890","totalPrice":1159890}]}

Ab har car ke SAARE variant + fuel + transmission combos chahiye, taaki har ek
pe getCarPrice POST karke price le sakein.

Honda ka check-price/<car> page pe ye combos dropdown me aate hain — kisi
options-API ya embedded __NEXT_DATA__ se. Ye script har car ke check-price page
pe jaake:
  1. Saare JSON API capture karta hai (jisme variant/fuel/transmission ho)
  2. __NEXT_DATA__ me variant/fuel/transmission data dhoondta hai
  3. Jo getCarPrice calls khud fire hote hain unki body record karta hai

Sab honda_variants.txt me save.

CHALAO:
    python debug_honda_variants.py
Phir honda_variants.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import json, re

BASE = "https://www.hondacarindia.com"
# check-price/<car> — yahan variant/fuel/transmission dropdown aate hain
CARS = ["honda-city", "honda-amaze", "honda-elevate", "honda-zrv", "honda-amaze-2g"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def looks_useful(body):
    low = body.lower()
    return any(k in low for k in ["variant", "fueltype", "transmission",
                                  "grade", "mt (manual)", "cvt", "e:hev", "vtec"])


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    api_hits = []
    getcarprice_bodies = []

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["google","gtm","facebook","gstatic","fonts","youtube",
                                "analytics","clarity","yellow","twitter","outbrain",
                                "treasuredata","mathtag","amazon","incapsula"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            body = resp.text()
        except Exception:
            return
        if "getCarPrice" in u:
            getcarprice_bodies.append((resp.request.post_data or "", body))
        elif looks_useful(body):
            api_hits.append((resp.url, body))

    page.on("response", on_response)

    for car in CARS:
        api_hits.clear()
        getcarprice_bodies.clear()
        url = f"{BASE}/check-price/{car}"
        log("\n" + "=" * 70)
        log(f"PAGE: {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  page status: {resp.status if resp else '?'}")
            page.wait_for_timeout(8000)
        except Exception as e:
            log(f"  goto fail: {str(e)[:60]}")
            continue

        # 1. useful JSON APIs
        log(f"\n  --- useful JSON APIs ({len(api_hits)}) ---")
        seen = set()
        for u, body in api_hits:
            base = u.split("?")[0]
            if base in seen:
                continue
            seen.add(base)
            log(f"  API: {u[:110]}")
            try:
                parsed = json.loads(body)
                log("  " + json.dumps(parsed, ensure_ascii=False)[:1500])
            except Exception:
                log("  " + body[:1200])

        # 2. getCarPrice auto-fires
        if getcarprice_bodies:
            log(f"\n  --- getCarPrice auto-calls ({len(getcarprice_bodies)}) ---")
            for post, body in getcarprice_bodies:
                log(f"  POST body: {post}")
                log(f"  resp: {body[:200]}")

        # 3. __NEXT_DATA__ me variant/fuel/transmission
        try:
            nd = page.evaluate(
                "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
            if nd:
                # keys of interest ke around chunks dikhao
                for kw in ['"variant"', '"variantList"', '"fuelType"', '"transmission"',
                           '"variants"', '"grades"', '"carModelData"', '"priceCheckData"']:
                    i = nd.find(kw)
                    if i != -1:
                        log(f"\n  __NEXT_DATA__ around {kw}:")
                        log("  " + nd[max(0, i-30):i+600].replace("\n", " "))
        except Exception as e:
            log(f"  next_data err: {str(e)[:50]}")

    browser.close()

with open("honda_variants.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. honda_variants.txt UPLOAD kar do.")
print("=" * 60)