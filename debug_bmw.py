"""
debug_bmw.py — BMW India ka price structure dhoondo
====================================================
BMW India: 2/3/5/7 Series, X1/X3/X5/X7, i4/iX/i7 (EV), Z4, M-series.
Ye script site structure dekhta hai.

CHALAO:
    python debug_bmw.py
Phir bmw_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.bmw.in"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{7,8})\b', body) if 3000000 <= int(n) <= 90000000))


SKIP = ["google","gtm","facebook","gstatic","fonts","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing"]


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(40000)

    apis = []
    def on_response(resp):
        u = resp.url
        low = u.lower()
        if any(s in low for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b) and any(k in b.lower() for k in ["variant","price","model","series","vehicle"]):
                apis.append((u, b))
    page.on("response", on_response)

    log("BMW homepage...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=40000)
        log(f"  [{resp.status if resp else '?'}] {BASE} (final: {page.url})")
        page.wait_for_timeout(5000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        kws = ["price","all-models","models","3-series","5-series","x1","x3","x5","configurator","build"]
        mlinks = sorted(set(h for h in hrefs if any(m in h.lower() for m in kws)))
        log(f"  links ({len(mlinks)}):")
        for h in mlinks[:25]:
            log(f"    {h}")
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")
        mlinks = []

    targets = [h for h in mlinks if any(k in h.lower() for k in ["price","all-models","models"])][:3]
    if not targets:
        targets = [f"{BASE}/en/all-models.html"]

    for url in targets:
        apis.clear()
        log("\n" + "=" * 70)
        log(f"PAGE: {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=40000)
            log(f"  status: {resp.status if resp else '?'}")
            if not resp or resp.status != 200:
                continue
            page.wait_for_timeout(6000)
            for _ in range(8):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            if apis:
                log(f"  --- price API ({len(apis)}) ---")
                seen = set()
                for u, b in apis:
                    base = u.split("?")[0]
                    if base in seen: continue
                    seen.add(base)
                    log(f"    {u[:110]}")
                    log(f"      prices: {real_prices(b)[:12]}")
                    names = re.findall(r'"(?:name|model|series|title|modelName)"\s*:\s*"([^"]{2,45})"', b)
                    if names:
                        log(f"      names: {names[:10]}")

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            plines = [(i,l) for i,l in enumerate(lines) if ("₹" in l or "Rs" in l or "INR" in l) and re.search(r"\d", l)]
            if plines:
                log(f"  ₹ lines ({len(plines)}):")
                for i, l in plines[:15]:
                    prev = lines[i-1] if i>0 else ""
                    log(f"    [{prev[:22]}] -> {l[:40]}")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("bmw_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. bmw_debug.txt UPLOAD kar do.")
print("=" * 60)