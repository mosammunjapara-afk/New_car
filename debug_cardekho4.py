"""
debug_cardekho4.py — CarDekho ka internal variant-price API (exact per-variant)
================================================================================
Progress: CarDekho pe real prices confirmed (Swift 5.79-8.80L official se match).
Sidebar ranges mile. Ab har model ka EXACT per-variant price chahiye.

CarDekho ke paas internal JSON API hai (api.cardekho.com / gaadi.com backend) jo
variant list + exact price deta hai. Ye script model page load pe jo bhi
XHR/fetch calls jaate hain (api.cardekho, gaadi, /api/) unhe capture karta hai —
khaas kar jinme variantId + exact price ho.

CHALAO:
    python debug_cardekho4.py
Phir cardekho_debug4.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.cardekho.com"
MODELS = [
    ("Skoda Kushaq", "skoda", "kushaq"),
    ("Maruti Swift", "maruti-suzuki", "swift"),
]

# ye domains/paths pe price API hone ka chance
API_HINT = ["api.cardekho", "gaadi", "/api/", "variant", "price", "usedcar",
            "newcar", "pricelist", "modeldetail", "getvariant"]

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
        "clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing","taboola",
        "criteo","crazyegg","connecto","vdo.ai","performoo","moengage","clevertap",
        "branch","scorecardresearch","amazon-adsystem","facebook","tags3"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def exact_prices(body):
    nums = re.findall(r'\b(\d{6,8})\b', body)
    return sorted(set(int(n) for n in nums if 100000 <= int(n) <= 99999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    calls = []
    def on_response(resp):
        u = resp.url
        low = u.lower()
        if any(s in low for s in SKIP):
            return
        is_hint = any(h in low for h in API_HINT)
        ct = resp.headers.get("content-type", "")
        if "json" not in ct and not is_hint:
            return
        try:
            b = resp.text()
        except Exception:
            return
        # variant-price data?
        if (exact_prices(b) and any(k in b.lower() for k in
                ["variant","price","fuel","transmission"])) or is_hint:
            calls.append((u, resp.request.method, b))
    page.on("response", on_response)

    for name, make, model in MODELS:
        calls.clear()
        log("\n" + "=" * 70)
        log(f"MODEL: {name}")
        log("=" * 70)
        url = f"{BASE}/{make}/{model}/price"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1400)
                page.wait_for_timeout(600)
            # "View all variants" / variant tab click
            for label in ["All Variants", "View all variants", "Variants",
                          "Compare Variants", "Show all variants"]:
                try:
                    el = page.locator(f"text={label}").first
                    if el.count() > 0:
                        el.click(timeout=2500)
                        page.wait_for_timeout(3000)
                except Exception:
                    pass
            page.wait_for_timeout(2000)

            # captured API calls — jinme sabse zyada exact prices
            hits = [(u, m, b, exact_prices(b)) for (u, m, b) in calls]
            hits.sort(key=lambda x: -len(x[3]))
            log(f"  captured API calls: {len(calls)}")
            seen = set()
            shown = 0
            for u, m, b, gp in hits:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                shown += 1
                if shown > 8:
                    break
                log(f"\n  [{m}] {u[:130]}")
                log(f"  {len(gp)} exact prices: {gp[:15]}")
                # variant naam bhi dikhao agar ho
                vnames = re.findall(r'"variant\w*[Nn]ame"\s*:\s*"([^"]{2,40})"', b)
                if vnames:
                    log(f"  variant names: {vnames[:12]}")
                log(f"  body: {b[:400].replace(chr(10),' ')}")

            # koi price-hint URL jo capture hua (bina price ke bhi) — list
            log("\n  --- saare hint-URLs (price API candidates) ---")
            seen2 = set()
            for u, m, b in calls:
                if any(h in u.lower() for h in ["api.cardekho","gaadi","/api/","variant","pricelist"]):
                    base = u.split("?")[0]
                    if base in seen2:
                        continue
                    seen2.add(base)
                    log(f"    [{m}] {u[:120]}")
        except Exception as e:
            log(f"  fail: {str(e)[:60]}")

    browser.close()

with open("cardekho_debug4.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug4.txt UPLOAD kar do.")
print("=" * 60)