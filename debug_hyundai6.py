"""
debug_hyundai6.py — Form fill karke "Prices" dabao, variant API pakdo
======================================================================
Creta price page pe form hai: Model/State/City/Fuel/Transmission + Prices button.
Ye script form ke dropdowns select karti hai, Prices dabati hai, aur jo API
call hota hai (variant prices ke liye) use pakadti hai.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://www.hyundai.com/in/en/find-a-car/creta/price"
api_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if "chat360" in u or "visualwebsite" in u or "google" in u:
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["variant", "grade", "exshowroom", "exprice", "showroomprice"]):
                    api_hits.append((u, body))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)

    # saare <select> dropdowns dhoondho
    selects = page.locator("select")
    n = selects.count()
    print(f"\n{n} dropdown mile")

    # har dropdown me pehla non-empty option select karo (State, City, Fuel, Transmission)
    for i in range(n):
        try:
            sel = selects.nth(i)
            options = sel.locator("option")
            opt_count = options.count()
            # pehla aisa option jo placeholder na ho
            for j in range(1, opt_count):
                val = options.nth(j).get_attribute("value")
                txt = options.nth(j).inner_text()
                if val and val.strip() and "select" not in txt.lower():
                    sel.select_option(index=j)
                    print(f"  dropdown[{i}]: '{txt}' select kiya")
                    page.wait_for_timeout(1500)
                    break
        except Exception as e:
            print(f"  dropdown[{i}] err: {str(e)[:40]}")

    page.wait_for_timeout(2000)

    # "Prices" button dhoondh ke click karo
    print("\n'Prices' button click karte hain...")
    for sel in ["text=Prices", "button:has-text('Prices')", "a:has-text('Prices')"]:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                el.click(timeout=4000)
                print(f"  clicked: {sel}")
                page.wait_for_timeout(4000)
                break
        except Exception:
            pass

    page.wait_for_timeout(3000)

    print(f"\n=== {len(api_hits)} variant-API calls mile ===")
    seen = set()
    saved = False
    for u, body in api_hits:
        base = u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"\n  URL: {u[:110]}")
        print(f"  preview: {body[:220]}")
        if not saved:
            with open("hyundai_variants.json", "w", encoding="utf-8") as f:
                f.write(body)
            print("  ^^ Saved: hyundai_variants.json")
            saved = True

    # page pe jo dikha wo bhi save karo
    txt = page.inner_text("body")
    with open("hyundai_price_page.txt", "w", encoding="utf-8") as f:
        f.write(txt)

    browser.close()
    print("\nDONE. 'hyundai_variants.json' ya 'hyundai_price_page.txt' bhej do.")