"""
debug_mahindra_source.py — Mahindra ke liye AUTOMATIC price source dhoondo
===========================================================================
Manual nahi chahiye — automatic source chahiye (jaise LR ka PDF-link).
Ye script Mahindra model page pe SAARE links check karta hai:
  - koi PDF (price-list)
  - koi "download price", "price list", brochure-with-price
  - koi external price-source link
Aur page ka poora embedded JSON/script bhi scan karta hai price ke liye.

CHALAO:
    python debug_mahindra_source.py
Phir mahindra_source.txt UPLOAD kar do.
"""

from playwright.sync_api import sync_playwright
import re

out = []
def log(s=""):
    print(s); out.append(str(s))


def rp(b):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b', b) if 500000 <= int(n) <= 9999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(35000)

    # Scorpio N (bada model) pe deep dive
    URL = "https://auto.mahindra.com/suv/scorpio-n/SCN.html"
    log(f"PAGE: {URL}")
    try:
        page.goto(URL, wait_until="domcontentloaded", timeout=35000)
        page.wait_for_timeout(7000)
        for _ in range(10):
            page.mouse.wheel(0, 900); page.wait_for_timeout(500)
        page.wait_for_timeout(3000)

        # 1. saare links — PDF, price, download, brochure
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        interesting = sorted(set(h for h in hrefs if any(k in h.lower() for k in
                        ["pdf","price","download","brochure","pricelist","price-list"])))
        log(f"\n  price/PDF/download links ({len(interesting)}):")
        for h in interesting[:15]:
            log(f"    {h[:120]}")

        # 2. price-list / price button click karke dekho
        for label in ["Price", "View Price", "Price List", "Download Price", "Check Price", "Explore Price"]:
            try:
                el = page.locator(f"text=/{label}/i").first
                if el.count() > 0:
                    log(f"\n  clicking '{label}'...")
                    el.click(timeout=3000)
                    page.wait_for_timeout(4000)
                    # naye links / URL change
                    log(f"    URL ab: {page.url[:90]}")
                    # ₹ aaya?
                    txt = page.inner_text("body")
                    pl = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d{5,}", l)]
                    if pl:
                        log(f"    ₹ lines: {len(pl)}")
                        for l in pl[:10]: log(f"      {l[:50]}")
                    break
            except Exception:
                pass

        # 3. embedded script/JSON me price (window.__DATA__, next data, inline)
        html = page.content()
        # bade JSON blobs me price
        prices_in_html = rp(html)
        log(f"\n  HTML me price-range numbers: {prices_in_html[:15]}")
        if prices_in_html:
            # ek price ke around ka context
            for pr in prices_in_html[:3]:
                i = html.find(str(pr))
                ctx = re.sub(r"<[^>]+>", " ", html[max(0,i-80):i+20])
                ctx = re.sub(r"\s+", " ", ctx)
                log(f"    {pr}: ...{ctx[-70:]}")
    except Exception as e:
        log(f"  fail: {str(e)[:45]}")

    browser.close()

with open("mahindra_source.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. mahindra_source.txt UPLOAD kar do.")