"""
debug_cardekho7.py — CarDekho variant list ko LIVE trigger karke pakdo
=======================================================================
Variant-table JS se on-demand load hoti hai. Ye script:
  1. Kushaq /price page pe "Kushaq Variants" / "Price List" heading tak SCROLL
     karta hai (taaki us section ka lazy data load ho)
  2. Us waqt jo bhi network call aaye (json/html) capture karta hai
  3. Saath hi known CarDekho variant URL patterns bhi try karta hai:
       /skoda/kushaq/specifications , /skoda/kushaq/variants , compare
  4. Jaha bhi "variantName + non-empty price" mile, dikhata hai

CHALAO:
    python debug_cardekho7.py
Phir cardekho_debug7.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.cardekho.com"
MODEL = ("Skoda Kushaq", "skoda", "kushaq", "Kushaq")

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
        "clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing","taboola",
        "criteo","crazyegg","connecto","vdo.ai","performoo","moengage","clevertap",
        "branch","scorecardresearch","amazon-adsystem","tags3","imasdk","recaptcha"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def variant_pairs(text):
    """variantName + variantPrice (non-empty) pairs nikaalo."""
    pairs = re.findall(
        r'"variantName"\s*:\s*"([^"]{2,45})"[^{}]*?"variantPrice"\s*:\s*"([^"]{2,20})"',
        text)
    # minComparePrice (exact rupee) bhi
    pairs2 = re.findall(
        r'"variantName"\s*:\s*"([^"]{2,45})"[^{}]*?"minComparePrice"\s*:\s*(\d{5,8})',
        text)
    return pairs, pairs2


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    name, make, model, mname = MODEL
    captured_bodies = []

    def on_response(resp):
        u = resp.url
        if any(s in u.lower() for s in SKIP):
            return
        try:
            b = resp.text()
        except Exception:
            return
        if '"variantName"' in b and '"variantPrice"' in b:
            captured_bodies.append((u, b))
    page.on("response", on_response)

    # ---- 1. price page, variant section tak scroll ----
    url = f"{BASE}/{make}/{model}/price"
    log("=" * 70)
    log(f"MODEL: {name}")
    log("=" * 70)
    log(f"\n[A] /price page, variant section tak scroll")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)

        # heading "Kushaq ... Variant" / "Price List" tak scroll
        for target in [f"{mname} Price List", f"{mname} Variants",
                       "Variants", "Price List", "Variant Price"]:
            try:
                el = page.locator(f"text={target}").first
                if el.count() > 0:
                    el.scroll_into_view_if_needed(timeout=3000)
                    log(f"  scrolled to '{target}'")
                    page.wait_for_timeout(3000)
                    break
            except Exception:
                pass

        # thoda thoda scroll (lazy load)
        for _ in range(12):
            page.mouse.wheel(0, 900)
            page.wait_for_timeout(500)
        page.wait_for_timeout(3000)

        # expand buttons
        for label in ["View all variants", "All Variants", "Show all",
                      "View More Variants", "Read More"]:
            try:
                el = page.locator(f"text={label}").first
                if el.count() > 0:
                    el.click(timeout=2500)
                    page.wait_for_timeout(2500)
            except Exception:
                pass

        # ab page ke HTML me variantName+price?
        html = page.content()
        pairs, pairs2 = variant_pairs(html)
        # sirf is model ke (dusre models ke carousel se bachne ke liye — sab dikhao)
        log(f"  HTML me variantName+variantPrice pairs: {len(pairs)}")
        seen = set()
        for vn, pr in pairs:
            k = vn[:25]
            if k in seen: continue
            seen.add(k)
            log(f"    {vn}  —  {pr}")
        log(f"  HTML me variantName+minComparePrice (exact ₹): {len(pairs2)}")
        seen = set()
        for vn, pr in pairs2:
            k = vn[:25]
            if k in seen: continue
            seen.add(k)
            log(f"    {vn}  —  ₹{pr}")
    except Exception as e:
        log(f"  fail: {str(e)[:60]}")

    # ---- 2. captured network bodies ----
    log(f"\n[B] network bodies with variantName+price: {len(captured_bodies)}")
    for u, b in captured_bodies[:3]:
        pairs, pairs2 = variant_pairs(b)
        log(f"  URL: {u[:110]}")
        log(f"    {len(pairs)} name+price, {len(pairs2)} name+exact")
        for vn, pr in (pairs2[:15] or pairs[:15]):
            log(f"      {vn}  —  {pr}")

    # ---- 3. known variant URL patterns ----
    log(f"\n[C] known variant-URL patterns try")
    for path in [f"/{make}/{model}/specifications", f"/{make}/{model}/variants",
                 f"/{make}/{model}"]:
        try:
            r = page.evaluate("""async (u) => {
                try { const x = await fetch(u); const t = await x.text();
                    return {status:x.status, len:t.length,
                            has: t.includes('"variantName"') && t.includes('"variantPrice"')}; }
                catch(e){ return {status:-1, err:String(e)}; }
            }""", BASE + path)
            log(f"  {path} -> {r}")
        except Exception as e:
            log(f"  {path} err: {str(e)[:40]}")

    browser.close()

with open("cardekho_debug7.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. cardekho_debug7.txt UPLOAD kar do.")
print("=" * 60)