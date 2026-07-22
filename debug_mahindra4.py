"""
debug_mahindra4.py — Mahindra ko VISIBLE browser me kholo (bot-detection bypass)
=================================================================================
Headless browser ko Mahindra blank deti hai (bot-detection). Ye script asli
DIKHNE WALA browser kholti hai (headless=False) — jaisa aapka Chrome. Isse
website ko lagta hai asli user hai, poora content deti hai.

NOTE: Ye chalega to ek Chrome window khulegi (khud). Usko band mat karna,
apne aap band hogi. Bas dekhte rehna.
"""
from playwright.sync_api import sync_playwright
import re

URL = "https://auto.mahindra.com/suv/xuv3xo/X3XO.html"
api_hits = []

with sync_playwright() as p:
    # headless=False = asli dikhne wala browser
    browser = p.chromium.launch(headless=False)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","evergage","qualtrics"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price","variant","exshowroom","showroom","mrp"]):
                    api_hits.append((u, body[:250]))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain (VISIBLE browser): {URL}")
    print("Ek Chrome window khulegi — usko band mat karna!")
    page.goto(URL, timeout=90000)
    page.wait_for_timeout(8000)

    # scroll to variants-pricing
    for i in range(15):
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(700)
    page.wait_for_timeout(4000)

    try:
        page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=20000)
        print("  ✓ ₹ price aa gaya!")
    except Exception:
        print("  ✗ ₹ nahi aaya")

    page.wait_for_timeout(3000)
    txt = page.inner_text("body")
    with open("mahindra_page_text.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"  Saved: mahindra_page_text.txt ({len(txt)} chars)")

    print("\n=== ₹-price lines ===")
    for line in txt.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            print("  ", repr(line.strip()[:55]))

    print("\n=== Variant-jaisi lines ===")
    for line in txt.split("\n"):
        l = line.strip()
        if re.match(r"^(MX|AX|REVX)", l) and len(l) < 20:
            print("  ", repr(l))

    print(f"\n=== {len(api_hits)} JSON API ===")
    seen=set()
    for u, prev in api_hits:
        base=u.split("?")[0]
        if base in seen: continue
        seen.add(base)
        print(f"  {u[:90]}")
        print(f"    {prev[:120]}")

    browser.close()
    print("\nDONE. mahindra_page_text.txt bhej do.")