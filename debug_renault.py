"""
debug_renault.py — Renault India ka price structure + API dhoondo
==================================================================
Renault India: Kwid, Triber, Kiger (+ naye). Ye script site ka structure
dekhta hai — model/price links, variant API, __NEXT_DATA__, ya ₹ prices.

CHALAO:
    python debug_renault.py
Phir renault_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.renault.co.in"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b', body) if 300000 <= int(n) <= 5000000))


SKIP = ["google","gtm","facebook","gstatic","fonts","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing"]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    apis = []
    def on_response(resp):
        u = resp.url
        if any(s in u.lower() for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            b = resp.text()
        except Exception:
            return
        if real_prices(b) and any(k in b.lower() for k in ["variant","price","trim","grade","model"]):
            apis.append((u, b))
    page.on("response", on_response)

    log("Renault homepage...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=50000)
        log(f"  [{resp.status if resp else '?'}] {BASE} (final: {page.url})")
        page.wait_for_timeout(5000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        models = ["kwid","triber","kiger","duster","price"]
        mlinks = sorted(set(h for h in hrefs if any(m in h.lower() for m in models)))
        log(f"  model/price links ({len(mlinks)}):")
        for h in mlinks[:20]:
            log(f"    {h}")
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")
        mlinks = []

    targets = [h for h in mlinks if any(k in h.lower() for k in ["price","kwid","triber","kiger"])][:4]
    if not targets:
        targets = [f"{BASE}/vehicles/kwid.html", f"{BASE}/cars/kwid"]

    for url in targets:
        apis.clear()
        log("\n" + "=" * 70)
        log(f"PAGE: {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            if not resp or resp.status != 200:
                continue
            page.wait_for_timeout(6000)
            for _ in range(6):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            hrefs2 = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
            plinks = sorted(set(h for h in hrefs2 if "price" in h.lower()))
            if plinks:
                log(f"  price links andar: {plinks[:4]}")

            if apis:
                log(f"  --- variant/price API ({len(apis)}) ---")
                seen = set()
                for u, b in apis:
                    base = u.split("?")[0]
                    if base in seen: continue
                    seen.add(base)
                    log(f"    {u[:100]}")
                    log(f"      prices: {real_prices(b)[:12]}")
                    names = re.findall(r'"(?:name|variantName|title|variant|grade)"\s*:\s*"([^"]{2,40})"', b)
                    if names:
                        log(f"      names: {names[:8]}")

            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
            if plines:
                log(f"  ₹ prices ({len(plines)}):")
                for l in plines[:10]:
                    log(f"    {l[:50]}")

            # __NEXT_DATA__
            try:
                nd = page.evaluate("() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                if nd and real_prices(nd):
                    log(f"  __NEXT_DATA__ me {len(real_prices(nd))} prices")
            except Exception:
                pass
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("renault_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. renault_debug.txt UPLOAD kar do.")
print("=" * 60)