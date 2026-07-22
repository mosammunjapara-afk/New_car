"""
debug_hyundai7.py — Form sahi se bharo (Maharashtra > Mumbai > Petrol > Manual), variant API pakdo
==================================================================================================
Dropdowns order me hain: [Model, State, City, Fuel, Transmission]
Har dropdown text se select karte hain (index se nahi), taaki sahi value jaye.
State/City select ke baad Fuel/Transmission populate hote hain — beech me wait.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://www.hyundai.com/in/en/find-a-car/creta/price"
api_hits = []

def sel_by_text(page, select_locator, wanted_list):
    """Dropdown me diye gaye texts me se jo mile, wo select karo. Return: selected text."""
    opts = select_locator.locator("option")
    n = opts.count()
    all_texts = []
    for j in range(n):
        t = (opts.nth(j).inner_text() or "").strip()
        all_texts.append(t)
    # pehle wanted list me se dhoondho
    for want in wanted_list:
        for j, t in enumerate(all_texts):
            if want.lower() in t.lower() and t.lower() not in ("", "state", "city", "fuel type", "transmission", "model"):
                select_locator.select_option(index=j)
                return t
    # nahi mila to pehla valid option
    for j in range(1, n):
        t = all_texts[j]
        if t and t.lower() not in ("state","city","fuel type","transmission","model"):
            select_locator.select_option(index=j)
            return t
    return None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","visualwebsite","google","doubleclick","cloudflare"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                body = resp.text()
                # variant price wala data (getModels ko chhod do — usme "category" hota hai har model)
                if any(k in body.lower() for k in ["exshowroom","showroomprice","variantname","gradename","grade","variant"]) \
                   and "getmodels" not in u.lower():
                    api_hits.append((u, body))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    selects = page.locator("select")
    n = selects.count()
    print(f"{n} dropdown mile\n")

    # Order: 0=Model, 1=State, 2=City, 3=Fuel, 4=Transmission (page order)
    if n >= 1:
        t = sel_by_text(page, selects.nth(0), ["New Creta", "Creta"])
        print(f"  Model: {t}")
        page.wait_for_timeout(2000)
    if n >= 2:
        t = sel_by_text(page, selects.nth(1), ["Maharashtra", "New Delhi", "Karnataka"])
        print(f"  State: {t}")
        page.wait_for_timeout(2500)  # city populate hone do
    if n >= 3:
        t = sel_by_text(page, selects.nth(2), ["Mumbai", "Pune", "Bengaluru", "Delhi"])
        print(f"  City: {t}")
        page.wait_for_timeout(2500)  # fuel populate hone do
    if n >= 4:
        t = sel_by_text(page, selects.nth(3), ["Petrol"])
        print(f"  Fuel: {t}")
        page.wait_for_timeout(2500)  # transmission populate
    if n >= 5:
        t = sel_by_text(page, selects.nth(4), ["Manual", "MT"])
        print(f"  Transmission: {t}")
        page.wait_for_timeout(2000)

    # Prices button
    print("\n'Prices' click...")
    for sel in ["text=Prices", "button:has-text('Prices')", "a:has-text('Prices')", "[class*='price']"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(timeout=4000)
                page.wait_for_timeout(4000)
                print(f"  clicked: {sel}")
                break
        except Exception:
            pass
    page.wait_for_timeout(3000)

    print(f"\n=== {len(api_hits)} variant-API calls ===")
    seen=set(); saved=False
    for u, body in api_hits:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  URL: {u[:110]}")
        print(f"  preview: {body[:250]}")
        if not saved:
            with open("hyundai_variants.json","w",encoding="utf-8") as f:
                f.write(body)
            print("  ^^ Saved: hyundai_variants.json")
            saved=True

    # page text bhi (agar variants page pe dikh rahe hon)
    with open("hyundai_price_page.txt","w",encoding="utf-8") as f:
        f.write(page.inner_text("body"))

    browser.close()
    print("\nDONE. hyundai_variants.json ya hyundai_price_page.txt bhej do.")