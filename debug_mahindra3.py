"""
debug_mahindra3.py — Mahindra XUV 3XO ko poora load hone de ke variants pakdo
==============================================================================
Page heavy hai, dheere load hota hai. Isliye:
  - zyada wait (networkidle + extra)
  - variants-pricing section tak scroll aur wait
  - "Explore All Variants" button click try
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
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","evergage","qualtrics"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price","variant","exshowroom","showroom","mrp","model"]):
                    api_hits.append((u, body[:250]))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)  # default load
    print("  Page khula, ab poora load hone dete hain (30 sec)...")
    page.wait_for_timeout(10000)

    # dheere-dheere poora scroll (heavy page)
    for i in range(20):
        page.mouse.wheel(0, 800)
        page.wait_for_timeout(800)
    page.wait_for_timeout(5000)

    # "₹" text aane ka wait
    try:
        page.wait_for_function("() => document.body.innerText.includes('₹')", timeout=20000)
        print("  ✓ ₹ price text aa gaya!")
    except Exception:
        print("  ✗ ₹ text 20 sec me nahi aaya")

    page.wait_for_timeout(3000)
    txt = page.inner_text("body")
    with open("mahindra_page_text.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"  Saved: mahindra_page_text.txt ({len(txt)} chars)")

    # ₹ price lines
    print("\n=== ₹-price lines ===")
    cnt = 0
    for line in txt.split("\n"):
        if "₹" in line and re.search(r"\d", line):
            print("  ", repr(line.strip()[:55]))
            cnt += 1
    if cnt == 0:
        print("  (abhi bhi koi price nahi — page aur bhi dheere hai)")

    # variant naam wali chhoti lines
    print("\n=== Variant-jaisi lines (MX/AX/REVX) ===")
    for line in txt.split("\n"):
        l = line.strip()
        if re.match(r"^(MX|AX|REVX|AX7|AX5)", l) and len(l) < 20:
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