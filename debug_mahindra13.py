"""
debug_mahindra13.py — Thar STEALTH mode me (bot-detection bypass)
==================================================================
Mahindra shayad automation detect karke blank deta hai. Stealth mode
browser ko asli-user jaisa banata hai. Isse content aa sakta hai.
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import re

URL = "https://auto.mahindra.com/suv/thar/THRN.html"
all_urls = []

# Stealth ke saath
with Stealth().use_sync(sync_playwright()) as p:
    browser = p.chromium.launch(headless=True, args=[
        "--disable-blink-features=AutomationControlled",
    ])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1400, "height": 900},
    )

    def on_response(resp):
        u = resp.url
        if re.search(r"\.(png|jpg|jpeg|gif|svg|woff2?|ttf|css|mp4|webp|ico)(\?|$)", u.lower()):
            return
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","google","gstatic","fonts","qualtrics"]):
            return
        if any(k in u.lower() for k in ["product-","json","/api/","variant","price","modal"]):
            all_urls.append(u)

    page.on("response", on_response)

    print(f"Kholte hain (STEALTH): {URL}")
    page.goto(URL, timeout=90000)
    print("  Wait (60 sec)...")
    for i in range(20):
        page.wait_for_timeout(3000)
        page.mouse.wheel(0, 600)

    txt = page.inner_text("body")
    print(f"\n  Page text: {len(txt)} chars")
    with open("mahindra_thar.txt", "w", encoding="utf-8") as f:
        f.write(txt)

    print("\n=== variant/₹ lines ===")
    cnt = 0
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if "₹" in l and re.search(r"\d", l):
            prev = lines[i-1] if i>0 else ""
            print(f"  [{prev[:22]}] {l[:38]}")
            cnt += 1
        elif re.match(r"^(AX|LX|MX|REVX|N\d)", l) and len(l) < 18:
            print(f"  variant: {l}")
            cnt += 1
    if cnt == 0:
        print("  (kuch nahi — stealth se bhi content nahi aaya)")

    print(f"\n=== data URLs ({len(all_urls)}) ===")
    seen=set()
    for u in all_urls:
        b=u.split("?")[0]
        if b in seen: continue
        seen.add(b)
        print(" ", u[:110])

    browser.close()
    print("\nDONE.")