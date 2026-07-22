"""
debug_citroen.py — Citroen India ka price structure dhoondo
============================================================
Citroen India: C3, C3 Aircross, Basalt, Aircross, eC3, Basalt Dark Edition.
Multi-model brand. Ye script site ka structure dekhta hai.

CHALAO:
    python debug_citroen.py
Phir citroen_debug.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.citroen.in"

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,7})\b', body) if 300000 <= int(n) <= 3000000))


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
        low = u.lower()
        if "rplug" in low or "slice" in low or "/agg/" in low:
            try:
                b = resp.text()
            except Exception:
                b = ""
            if real_prices(b):
                apis.append((u, b))
            return
        if any(s in low for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b) and any(k in b.lower() for k in ["variant","price","version","grade","model"]):
                apis.append((u, b))
    page.on("response", on_response)

    log("Citroen homepage...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=50000)
        log(f"  [{resp.status if resp else '?'}] {BASE} (final: {page.url})")
        page.wait_for_timeout(5000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        models = ["c3","aircross","basalt","ec3","price"]
        mlinks = sorted(set(h for h in hrefs if any(m in h.lower() for m in models)))
        log(f"  model/price links ({len(mlinks)}):")
        for h in mlinks[:20]:
            log(f"    {h}")
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")
        mlinks = []

    targets = [h for h in mlinks if any(k in h.lower() for k in ["price","c3","basalt","aircross"])][:4]
    if not targets:
        targets = [f"{BASE}/c3.html", f"{BASE}/basalt.html"]

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
            for _ in range(8):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            hrefs2 = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
            plinks = sorted(set(h for h in hrefs2 if "price" in h.lower()))
            if plinks:
                log(f"  price links andar: {plinks[:4]}")

            if apis:
                log(f"  --- price API ({len(apis)}) ---")
                seen = set()
                for u, b in apis:
                    base = u.split("?")[0]
                    if base in seen: continue
                    seen.add(base)
                    log(f"    {u[:110]}")
                    log(f"      prices: {real_prices(b)[:15]}")
                    names = re.findall(r'"(?:name|label|version|variant|grade|title)"\s*:\s*"([^"]{2,40})"', b)
                    if names:
                        log(f"      names: {names[:12]}")

            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            plines = [(i,l) for i,l in enumerate(lines) if "₹" in l and re.search(r"\d", l)]
            if plines:
                log(f"  ₹ lines ({len(plines)}):")
                for i, l in plines[:15]:
                    prev = lines[i-1] if i>0 else ""
                    log(f"    [{prev[:22]}] -> {l[:38]}")
            # Citroen trims
            for trim in ["Live","Feel","Shine","You","Plus","Max","Dark Edition"]:
                if re.search(r"\b"+re.escape(trim)+r"\b", txt):
                    log(f"    (trim: {trim})")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("citroen_debug.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. citroen_debug.txt UPLOAD kar do.")
print("=" * 60)