"""
debug_mercedes2.py — Mercedes onesearch GraphQL ki poori response
==================================================================
MIL GAYA! Mercedes GraphQL:
  https://ap.api.oneweb.mercedes-benz.com/commerce/onesearch/graphql
  (search-results page pe fire, variant + exact price)

Ye script search-results page (all vehicles) khol ke us GraphQL ki POORI
response capture karta hai — variant naam + price + fuel structure ke liye.

CHALAO:
    python debug_mercedes2.py

Banega: mercedes_gql.json + mercedes2.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

# saare vehicles (price-asc) — ek page pe saare models
URL = "https://www.mercedes-benz.co.in/passengercars/buy/new-car/search-results.html/?emhsortType=price-asc&emhvehicleCategory=vehicles"

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
    page.set_default_timeout(40000)

    gql_responses = []
    def on_response(resp):
        if "onesearch/graphql" in resp.url:
            try:
                gql_responses.append(resp.text())
            except Exception:
                pass
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(6000)
        # sab load karne ke liye khoob scroll
        for _ in range(15):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(700)
        page.wait_for_timeout(4000)
    except Exception as e:
        log(f"  fail: {str(e)[:50]}")

    log(f"\nGraphQL responses captured: {len(gql_responses)}")
    # sabse bada (jisme sabse zyada data)
    gql_responses.sort(key=len, reverse=True)
    if gql_responses:
        with open("mercedes_gql.json", "w", encoding="utf-8") as f:
            f.write(gql_responses[0])
        log(f"saved biggest: mercedes_gql.json ({len(gql_responses[0])} chars)")
        # structure samajho
        try:
            data = json.loads(gql_responses[0])
            # products/vehicles dhoondo
            def find_products(o, path="", depth=0):
                if depth > 6:
                    return
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k.lower() in ("products", "vehicles", "items", "results", "hits") and isinstance(v, list) and v:
                            log(f"\n  {path}.{k}: {len(v)} items")
                            it = v[0]
                            if isinstance(it, dict):
                                log(f"    item keys: {list(it.keys())[:20]}")
                                log(f"    item sample: {json.dumps(it)[:500]}")
                        find_products(v, path+"."+k, depth+1)
                elif isinstance(o, list):
                    for x in o[:2]:
                        find_products(x, path+"[]", depth+1)
            find_products(data)
        except Exception as e:
            log(f"  parse note: {str(e)[:50]}")

    browser.close()

with open("mercedes2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. mercedes_gql.json + mercedes2.txt UPLOAD karo.")
print("=" * 60)