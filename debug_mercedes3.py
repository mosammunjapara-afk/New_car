"""
debug_mercedes3.py — Mercedes ki SAARI GraphQL calls, price wali dhoondo
========================================================================
search-results query me price nahi tha. Debug1 me prices dikhe the (C 200
5990000...) — wo ek ALAG onesearch/graphql call se. Ye script SAARI graphql
calls capture karta hai aur jisme price-range numbers + variant naam ho use
dikhata hai + save karta hai.

CHALAO:
    python debug_mercedes3.py

Banega: mercedes_price_gql.json + mercedes3.txt — UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re, json

URL = "https://www.mercedes-benz.co.in/passengercars/buy/new-car/search-results.html/?emhsortType=price-asc&emhvehicleCategory=vehicles"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def prices(s):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{7,8})\b', s) if 2000000 <= int(n) <= 90000000))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(40000)

    gql_calls = []  # (request_body, response_body)
    def on_response(resp):
        if "onesearch/graphql" in resp.url or "vmos-api" in resp.url:
            try:
                req = resp.request.post_data or ""
            except Exception:
                req = ""
            try:
                body = resp.text()
            except Exception:
                body = ""
            gql_calls.append((resp.url, req, body))
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=40000)
        page.wait_for_timeout(6000)
        for _ in range(15):
            page.mouse.wheel(0, 1200)
            page.wait_for_timeout(700)
        page.wait_for_timeout(4000)
    except Exception as e:
        log(f"  fail: {str(e)[:50]}")

    log(f"\nGraphQL/vmos calls: {len(gql_calls)}")
    best = None
    for url, req, body in gql_calls:
        pr = prices(body)
        # operation naam
        op = re.search(r'"operationName"\s*:\s*"([^"]+)"', req)
        opn = op.group(1) if op else "?"
        # variant naam (C 200 / GLA 200 type)
        names = re.findall(r'"name"\s*:\s*"([A-Z][A-Za-z0-9 ]{1,25}\d[A-Za-z0-9 ]{0,10})"', body)
        log(f"\n  op={opn}  url={url.split('/')[-1][:30]}  prices={len(pr)}  names={len(names)}")
        if pr:
            log(f"     prices: {pr[:12]}")
            log(f"     names: {list(dict.fromkeys(names))[:12]}")
            if best is None or len(pr) > len(prices(best[2])):
                best = (url, req, body)

    if best:
        with open("mercedes_price_gql.json", "w", encoding="utf-8") as f:
            f.write(best[2])
        log(f"\n  saved price-wali response: mercedes_price_gql.json ({len(best[2])} chars)")
        # request query bhi (taaki scraper me use kar sakein)
        with open("mercedes_price_query.txt", "w", encoding="utf-8") as f:
            f.write(best[1])
        log(f"  saved request query: mercedes_price_query.txt")
        # structure
        try:
            data = json.loads(best[2])
            def find_list(o, path="", depth=0):
                if depth > 7: return
                if isinstance(o, dict):
                    for k, v in o.items():
                        if isinstance(v, list) and v and isinstance(v[0], dict):
                            keys = list(v[0].keys())
                            s = json.dumps(v[0])
                            if prices(s) or 'name' in [kk.lower() for kk in keys]:
                                log(f"    LIST {path}.{k}: {len(v)} items, keys={keys[:12]}")
                                log(f"      item: {s[:400]}")
                        find_list(v, path+"."+k, depth+1)
                elif isinstance(o, list):
                    for x in o[:1]:
                        find_list(x, path+"[]", depth+1)
            find_list(data)
        except Exception as e:
            log(f"  parse note: {str(e)[:50]}")
    else:
        log("\n  koi price-wali graphql call nahi mili")

    browser.close()

with open("mercedes3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. mercedes_price_gql.json + mercedes_price_query.txt + mercedes3.txt UPLOAD karo.")
print("=" * 60)