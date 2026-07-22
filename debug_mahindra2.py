"""
debug_mahindra2.py — XUV 3XO ke variants + prices pakadna
==========================================================
URL: auto.mahindra.com/suv/xuv3xo/X3XO.html#variants-pricing
Variants tabs (MX1, REVX M, AX7L...) pe click karke price capture karte hain.
Network API + page text dono dekhte hain.
"""
from playwright.sync_api import sync_playwright
import re

URL = "https://auto.mahindra.com/suv/xuv3xo/X3XO.html"
api_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","google","doubleclick","gtm","analytics","facebook","evergage","qualtrics"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price","variant","exshowroom","showroom","mrp"]):
                    api_hits.append((u, body[:200]))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    # variants-pricing section tak scroll
    for _ in range(10):
        page.mouse.wheel(0, 1000); page.wait_for_timeout(600)
    page.wait_for_timeout(3000)

    # poora text save karo
    txt = page.inner_text("body")
    with open("mahindra_page_text.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"Saved: mahindra_page_text.txt ({len(txt)} chars)")

    # variant tabs dhoondho aur click karke price dekho
    # tabs: MX1, REVX M, REVX M (O), MX2, MX2 PRO, MX3, MX3 PRO, REVX A, AX5L, AX7, AX7L
    variant_names = ["MX1","REVX M (O)","REVX M","MX2 PRO","MX2","MX3 PRO","MX3","REVX A","AX5L","AX7L","AX7"]
    print("\n--- Variants pe click karke price dekhte hain ---")
    found_prices = {}
    for vn in variant_names:
        try:
            tab = page.get_by_text(vn, exact=True).first
            if tab.count() > 0:
                tab.click(timeout=3000)
                page.wait_for_timeout(1500)
                # abhi jo price dikh raha hai (₹ wali line) capture karo
                cur = page.inner_text("body")
                # variant card ke aas-paas ₹ price
                m = re.findall(r"₹\s*[\d,]{5,}", cur)
                if m:
                    found_prices[vn] = m
        except Exception:
            pass

    print("\n=== Variant clicks se mile prices ===")
    for vn, prices in found_prices.items():
        print(f"  {vn}: {prices[:3]}")

    # saari ₹ lines text me
    print("\n=== Text me saari ₹-price lines ===")
    for line in txt.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            print("  ", repr(line.strip()[:50]))

    print(f"\n=== {len(api_hits)} JSON API ===")
    seen=set()
    for u, prev in api_hits:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"  {u[:90]}")
        print(f"    {prev[:100]}")

    browser.close()
    print("\nDONE. mahindra_page_text.txt bhej do.")