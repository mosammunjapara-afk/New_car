"""
debug_skoda2.py — Skoda ke ASLI URLs homepage se dhoondo (guessing nahi)
=========================================================================
Pichli baar guessed URLs 404 the. Ab homepage khol ke saare andar ke links
nikaalte hain, jinme 'price', 'model', 'kushaq', 'slavia' etc. ho — phir un
asli URLs pe jaake price data dekhte hain.

CHALAO:
    python debug_skoda2.py
Phir skoda_debug2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.skoda-auto.co.in"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def looks_price(body):
    return bool(re.search(r'\d{6,7}', body)) and any(
        k in body.lower() for k in ["variant", "price", "grade", "trim", "exshowroom"]
    )


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # 1. Homepage khol ke saare links nikaalo
    log("Homepage khol rahe hain...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
        log(f"homepage status: {resp.status if resp else '?'}")
        log(f"final URL: {page.url}")
        page.wait_for_timeout(5000)
    except Exception as e:
        log(f"homepage fail: {str(e)[:80]}")

    # saare anchor href nikaalo
    try:
        hrefs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).map(a => a.href);
        }""")
    except Exception:
        hrefs = []

    log(f"\ntotal links: {len(hrefs)}")
    # relevant links filter karo
    kw = ["price", "kushaq", "slavia", "kodiaq", "kylaq", "model", "variant", "config"]
    relevant = sorted(set(h for h in hrefs if any(k in h.lower() for k in kw)
                          and "skoda" in h.lower()))
    log(f"\n=== relevant links ({len(relevant)}) ===")
    for h in relevant[:40]:
        log(f"  {h}")

    # 2. price/model links pe jaake data dekho
    price_links = [h for h in relevant if any(k in h.lower() for k in
                   ["price", "kushaq", "slavia", "kodiaq", "kylaq"])][:6]

    apis = []
    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["google","gtm","facebook","gstatic","fonts","youtube",
                                "analytics","clarity","adobe","demdex","omtrdc","onetrust",
                                "cookie","hotjar","bing"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if looks_price(b):
                apis.append((u, b[:400]))
    page.on("response", on_response)

    for link in price_links:
        apis.clear()
        log("\n" + "=" * 70)
        log(f"VISIT: {link}")
        log("=" * 70)
        try:
            resp = page.goto(link, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)
            for _ in range(4):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            if apis:
                log(f"  --- price JSON APIs ({len(apis)}) ---")
                seen = set()
                for u, prev in apis:
                    base = u.split("?")[0]
                    if base in seen:
                        continue
                    seen.add(base)
                    log(f"  API: {u[:120]}")
                    log(f"       {prev[:250]}")

            # __NEXT_DATA__ / embedded
            try:
                nd = page.evaluate(
                    "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                if nd and looks_price(nd):
                    log(f"  __NEXT_DATA__ me price data (len {len(nd)})")
            except Exception:
                pass

            # page ₹ prices
            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
            if plines:
                log(f"  Page ₹ prices ({len(plines)}):")
                for l in plines[:15]:
                    log(f"    {l[:60]}")
        except Exception as e:
            log(f"  visit fail: {str(e)[:60]}")

    browser.close()

with open("skoda_debug2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug2.txt UPLOAD kar do.")
print("=" * 60)