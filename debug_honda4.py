"""
debug_honda4.py — Honda check-price form fill karke variant-price API pakdo
============================================================================
check-price pe State+City select karke "Check Price" dabate hain,
jo variant-price API call hota hai use pakadte hain (Hyundai jaisa).
"""
from playwright.sync_api import sync_playwright
import json, re

URL = "https://www.hondacarindia.com/check-price"
apis = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","google","doubleclick","gtm","facebook","gstatic","fonts","youtube"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                b = resp.text()
                # variant price data (bade number + variant/grade)
                if re.search(r'\d{6,7}', b) and any(k in b.lower() for k in ["variant","grade","price","exshowroom","trim"]):
                    apis.append((u, b[:300]))
            except Exception: pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)

    # dropdowns
    selects = page.locator("select")
    n = selects.count()
    print(f"{n} dropdown mile")
    for i in range(n):
        try:
            sel = selects.nth(i)
            opts = sel.locator("option")
            oc = opts.count()
            for j in range(1, oc):
                t = (opts.nth(j).inner_text() or "").strip()
                v = opts.nth(j).get_attribute("value")
                if v and t and "select" not in t.lower():
                    sel.select_option(index=j)
                    print(f"  dropdown[{i}]: '{t}'")
                    page.wait_for_timeout(2000)
                    break
        except Exception as e:
            print(f"  dropdown[{i}] err: {str(e)[:30]}")

    page.wait_for_timeout(1500)
    # "Check Price" button
    print("\n'Check Price' click...")
    for selc in ["text=Check Price", "button:has-text('Check Price')", "a:has-text('Check Price')"]:
        try:
            el = page.locator(selc).first
            if el.count() > 0:
                el.click(timeout=4000)
                print(f"  clicked: {selc}")
                page.wait_for_timeout(5000)
                break
        except Exception: pass
    page.wait_for_timeout(3000)

    print(f"\n=== {len(apis)} variant-price API ===")
    seen=set()
    for u, prev in apis:
        b=u.split("?")[0]
        if b in seen: continue
        seen.add(b)
        print(f"\n  {u[:110]}")
        print(f"  {prev[:200]}")

    # page pe variant prices dikhe?
    txt = page.inner_text("body")
    with open("honda_checkprice_result.txt","w",encoding="utf-8") as f: f.write(txt)
    print("\n=== Page pe ₹ prices ===")
    for line in txt.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            print("  ", repr(line.strip()[:50]))

    browser.close()
    print("\nDONE. Screenshot ya honda_checkprice_result.txt bhej do.")