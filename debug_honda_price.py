"""
debug_honda_price.py — Honda variant-price DHOONDO (do tarike ek saath)
========================================================================
Ab tak pata chala:
  - tech-specs.json me sirf STARTING price (variant-wise nahi)
  - check-price ke /api/ endpoints me price hai hi nahi (sirf state/city/dealer)

Honda ki har car ka apna PRICE PAGE hai: hondacarindia.com/<car>/price
Uske peeche variant-wise price hoti hai. Ye script HAR car ke liye:

  TARIKA 1: /_next/data/<BUILD_ID>/<car>/price.json  seedha kholta hai
            (Next.js yahan variant-price rakhta hai — clean JSON)
  TARIKA 2: agar #1 fail, to <car>/price page BROWSER me kholta hai,
            background API + page pe dikhne wale ₹ variant-prices dono pakadta hai

Sab kuch honda_price_result.txt me save hota hai.

CHALAO:
    python debug_honda_price.py

Phir honda_price_result.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import json, re

BASE = "https://www.hondacarindia.com"

# car slugs (tech-specs se + offer-cars se confirmed)
CARS = ["honda-city", "honda-amaze", "honda-amaze-2g",
        "honda-elevate", "honda-zrv", "honda-0-series"]

# price page ke liye alag-alag possible sub-paths (jo bhi chale)
PRICE_SUFFIXES = ["price", "select-variant", "variants", "on-road-price"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def get_build_id(page):
    """Homepage se live BUILD_ID nikaalo (roz badal sakta hai)."""
    try:
        page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        html = page.content()
        m = re.search(r'"buildId":"([^"]+)"', html)
        if m:
            return m.group(1)
    except Exception as e:
        log(f"  build id warn: {str(e)[:50]}")
    return "BASUSSBWMUt_vlP4OWNYX"  # fallback (purana)


def try_json(page, url):
    """Browser context me fetch karke JSON body lao."""
    try:
        return page.evaluate(
            """async (u) => {
                try {
                    const r = await fetch(u, {headers:{'Content-Type':'application/json'}});
                    return {status:r.status, body: await r.text()};
                } catch(e) { return {status:-1, body:String(e)}; }
            }""", url)
    except Exception as e:
        return {"status": -2, "body": str(e)}


def scan_prices(text):
    """Text me variant-jaisi price + naam dhoondo (quick check)."""
    prices = re.findall(r'"?(?:PN_Price|price|exShowroom|ex_showroom_price|amount)"?\s*[:=]\s*"?(\d{5,8})', text)
    return sorted(set(prices))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    BUILD_ID = get_build_id(page)
    log(f"BUILD_ID: {BUILD_ID}\n")

    # ---- TARIKA 1: har car ka har price-suffix ka _next/data JSON ----
    log("#" * 70)
    log("# TARIKA 1: _next/data price JSONs")
    log("#" * 70)
    good_json = {}
    for car in CARS:
        for suf in PRICE_SUFFIXES:
            url = f"{BASE}/_next/data/{BUILD_ID}/{car}/{suf}.json"
            res = try_json(page, url)
            st = res["status"]
            body = res["body"]
            if st == 200 and body.strip().startswith("{"):
                prices = scan_prices(body)
                mark = f"  <== {len(prices)} prices!" if len(prices) > 2 else ""
                log(f"[200] {car}/{suf}.json  (len {len(body)}){mark}")
                if len(prices) > 2:
                    good_json[f"{car}/{suf}"] = body
            # 404 wagaira silently skip

    # jo achhe JSON mile, unka structure dikhao
    for key, body in good_json.items():
        log("\n" + "=" * 70)
        log(f"GOOD JSON: {key}")
        log("=" * 70)
        try:
            parsed = json.loads(body)
            log(json.dumps(parsed, indent=2, ensure_ascii=False)[:5000])
        except Exception:
            log(body[:3000])

    # ---- TARIKA 2: price page browser me kholo, API + ₹ prices pakdo ----
    if not good_json:
        log("\n" + "#" * 70)
        log("# TARIKA 1 fail — TARIKA 2: price page kholke API pakdo")
        log("#" * 70)

        apis = []
        def on_resp(r):
            u = r.url
            if any(x in u for x in ["google","gtm","facebook","gstatic","fonts",
                                    "youtube","analytics","clarity","yellow","twitter",
                                    "outbrain","treasuredata","mathtag","amazon"]):
                return
            ct = r.headers.get("content-type", "")
            if "json" in ct:
                try:
                    b = r.text()
                    if re.search(r'\d{5,8}', b):
                        apis.append((u, b))
                except Exception:
                    pass
        page.on("response", on_resp)

        for car in CARS:
            apis.clear()
            url = f"{BASE}/{car}/price"
            log("\n" + "=" * 70)
            log(f"PAGE: {url}")
            log("=" * 70)
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
                log(f"  page status: {resp.status if resp else '?'}")
                page.wait_for_timeout(6000)
            except Exception as e:
                log(f"  goto fail: {str(e)[:60]}")
                continue

            # background APIs jo price-jaisi thi
            seen = set()
            for u, b in apis:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                prices = scan_prices(b)
                log(f"  API: {u[:100]}")
                if prices:
                    log(f"       prices: {prices[:15]}")
                    log(f"       preview: {b[:400]}")

            # page pe dikhne wale ₹ prices
            try:
                txt = page.inner_text("body")
                plines = [l.strip() for l in txt.split("\n")
                          if "₹" in l and re.search(r"\d", l)]
                if plines:
                    log("  Page ₹ prices:")
                    for l in plines[:25]:
                        log(f"    {l[:60]}")
            except Exception:
                pass

    browser.close()

with open("honda_price_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. honda_price_result.txt UPLOAD kar do.")
print("=" * 60)