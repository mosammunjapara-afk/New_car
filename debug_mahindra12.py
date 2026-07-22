"""
debug_mahindra12.py — Thar: iframe + lamba wait + saare frames ka content
==========================================================================
Thar ka content shayad iframe me ya bahut der se aata hai. Ye script:
  1. Saare frames (iframe bhi) check karti hai
  2. Har frame ka text me variant/₹ dhoondti hai
  3. Saare network URLs (bina filter) list karti hai — taaki data-source dikhe
"""
from playwright.sync_api import sync_playwright
import re

URL = "https://auto.mahindra.com/suv/thar/THRN.html"
all_urls = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        # sirf data-jaise (js/json/html/api), images/fonts chhod do
        if re.search(r"\.(png|jpg|jpeg|gif|svg|woff|woff2|ttf|css|mp4|webp|ico)(\?|$)", u.lower()):
            return
        if any(x in u for x in ["chat360","doubleclick","gtm","facebook","google","gstatic","fonts"]):
            return
        all_urls.append(u)

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)
    print("  Lamba wait (70 sec)...")
    for i in range(23):
        page.wait_for_timeout(3000)
        page.mouse.wheel(0, 600)

    # SAARE frames check karo (iframe included)
    print(f"\n=== {len(page.frames)} frames mile ===")
    for idx, frame in enumerate(page.frames):
        try:
            ftext = frame.inner_text("body") if frame != page.main_frame else ""
            # main frame alag se
        except Exception:
            ftext = ""
        try:
            ftext = frame.locator("body").inner_text(timeout=3000)
        except Exception:
            ftext = ""
        has_price = "₹" in ftext or re.search(r"MX\d|AX\d|REVX|N\d\d", ftext or "")
        print(f"  frame[{idx}]: {frame.url[:70]}  chars={len(ftext)}  variant/₹={'YES' if has_price else 'no'}")
        if has_price:
            print(f"    --- is frame me price/variant hai! ---")
            for line in (ftext or "").split("\n"):
                l = line.strip()
                if "₹" in l or re.match(r"^(MX|AX|REVX|N\d)", l):
                    print(f"      {l[:50]}")

    # data-source URLs (json/js/Product-)
    print(f"\n=== data-jaise URLs (Product/json/api) ===")
    seen = set()
    for u in all_urls:
        if any(k in u.lower() for k in ["product-", ".json", "/api/", "getvariant", "price", "modal"]):
            base = u.split("?")[0]
            if base in seen: continue
            seen.add(base)
            print(" ", u[:110])

    browser.close()
    print("\nDONE.")