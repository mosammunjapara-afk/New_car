"""
debug_mahindra6.py — 3D configurator ke SAARE network calls dekho
==================================================================
XUV700 configurator (XUV700.html) 3D hai, par price data kisi API se aata hai.
Ye script us page ke SAARE network responses dekhti hai (json, js, text — sab)
aur jisme price/variant jaisa data ho, use dhoondti hai.
"""
from playwright.sync_api import sync_playwright
import re, json

URL = "https://auto.mahindra.com/XUV700.html"
all_hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","evergage","qualtrics","google-analytics","gstatic","fonts"]):
            return
        # image/font/css skip
        if re.search(r"\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|css|mp4|webp)(\?|$)", u.lower()):
            return
        try:
            body = resp.text()
            # price/variant jaisa data (bade numbers, variant naam)
            low = body.lower()
            if any(k in low for k in ['"price"',"exshowroom","ex_showroom","showroomprice","variantprice"]) \
               or re.search(r'(mx|ax7|ax5|revx).{0,30}\d{6,}', low):
                all_hits.append((u, body))
        except Exception:
            pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)
    print("  3D configurator load hone dete hain (60 sec)...")
    # 3D bhaari hai, lamba wait + interaction
    for i in range(20):
        page.wait_for_timeout(3000)
        if i % 4 == 0:
            print(f"    ... {i*3} sec, ab tak {len(all_hits)} data-calls")
        # thoda scroll/mouse move taaki configurator active ho
        try:
            page.mouse.move(700, 400)
            page.mouse.wheel(0, 300)
        except Exception:
            pass

    print(f"\n=== {len(all_hits)} data-calls mile (price/variant jaisa) ===")
    seen = set()
    for u, body in all_hits:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        print(f"\n  URL: {u[:100]}")
        print(f"  size: {len(body)} chars")
        print(f"  preview: {body[:200]}")
        # sabse bade wale ko save karo
    if all_hits:
        # sabse bada body save karo (usme sab data hoga)
        biggest = max(all_hits, key=lambda x: len(x[1]))
        with open("mahindra_api_data.txt", "w", encoding="utf-8") as f:
            f.write(f"URL: {biggest[0]}\n\n{biggest[1]}")
        print(f"\n  Sabse bada data save hua: mahindra_api_data.txt ({len(biggest[1])} chars)")

    browser.close()
    print("\nDONE. mahindra_api_data.txt bhej do (agar bani).")
    if not all_hits:
        print("Koi price-data call nahi mila. 3D configurator data ko")
        print("bahut deep chhupata hai — ye brand manual/special hoga.")