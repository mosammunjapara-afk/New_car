"""
debug_jaguar.py — Jaguar India ka price structure dhoondo
==========================================================
Jaguar India: F-PACE, F-TYPE (aur kuch models discontinue ho rahe). JLR sibling
hai to ho sakta Land Rover jaisa findmeasuv PDF ho.

Ye script:
  1. Jaguar homepage se model + price/PDF links
  2. koi price-list PDF link
  3. model pages pe ₹ prices

CHALAO:
    python debug_jaguar.py
Phir jaguar_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.jaguar.in"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(35000)

    log("Jaguar homepage...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=35000)
        log(f"  [{resp.status if resp else '?'}] {BASE} (final: {page.url})")
        page.wait_for_timeout(5000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        # PDF / price / model links
        pdf_links = sorted(set(h for h in hrefs if ".pdf" in h.lower() or "pricing_pdf" in h.lower() or "findmeasuv" in h.lower()))
        model_links = sorted(set(h for h in hrefs if any(m in h.lower() for m in
                        ["f-pace","f-type","price","models","vehicles","xf","xe","i-pace"])))
        log(f"  PDF links ({len(pdf_links)}):")
        for h in pdf_links[:8]:
            log(f"    {h[:130]}")
        log(f"  model/price links ({len(model_links)}):")
        for h in model_links[:15]:
            log(f"    {h[:100]}")
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")
        pdf_links = []; model_links = []

    # model pages pe ₹
    for url in model_links[:3]:
        if ".pdf" in url.lower():
            continue
        log("\n" + "=" * 60)
        log(f"PAGE: {url}")
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=35000)
            log(f"  status: {resp.status if resp else '?'}")
            if not resp or resp.status != 200:
                continue
            page.wait_for_timeout(5000)
            for _ in range(6):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(500)
            # PDF/price link andar
            h2 = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
            pl = sorted(set(h for h in h2 if ".pdf" in h.lower() or "findmeasuv" in h.lower() or "price" in h.lower()))
            if pl:
                log(f"  price/PDF links andar:")
                for h in pl[:5]:
                    log(f"    {h[:120]}")
            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if ("₹" in l or "INR" in l) and re.search(r"\d{5,}", l)]
            for l in plines[:8]:
                log(f"  ₹: {l[:50]}")
        except Exception as e:
            log(f"  fail: {str(e)[:45]}")

    browser.close()

with open("jaguar_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. jaguar_debug.txt UPLOAD kar do.")
print("=" * 60)