"""
debug_nissan2.py — Nissan Magnite variant+price (prices.html se)
=================================================================
Mile URLs: nissan.in/vehicles/new/magnite/prices.html aur /prices-list.html
Ye script in pages pe jaake Magnite ke variant + price (XE/XL/XV/XV Premium +
Turbo/CVT) nikaalta hai.

CHALAO:
    python debug_nissan2.py
Phir nissan2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

PAGES = {
    "Magnite prices": "https://www.nissan.in/vehicles/new/magnite/prices.html",
    "Prices list": "https://www.nissan.in/prices-list.html",
}

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,7})\b', body) if 300000 <= int(n) <= 2000000))


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
        if any(s in low for s in ["google","gtm","facebook","font",".css",".png",".jpg",".svg","analytics","clarity"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b):
                apis.append((u, b))
    page.on("response", on_response)

    for name, url in PAGES.items():
        apis.clear()
        log("\n" + "=" * 70)
        log(f"PAGE: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(600)
            page.wait_for_timeout(3000)

            # JSON API
            if apis:
                log(f"  --- price JSON API ({len(apis)}) ---")
                seen = set()
                for u, b in apis:
                    base = u.split("?")[0]
                    if base in seen: continue
                    seen.add(base)
                    log(f"    {u[:100]}")
                    log(f"      prices: {real_prices(b)[:15]}")
                    names = re.findall(r'"(?:name|variant|version|grade|title)"\s*:\s*"([^"]{2,40})"', b)
                    if names:
                        log(f"      names: {names[:12]}")

            # page pe variant + ₹ (tables)
            txt = page.inner_text("body")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            plines = [(i,l) for i,l in enumerate(lines) if ("₹" in l or "Rs" in l) and re.search(r"\d{5,}", l)]
            log(f"  ₹/Rs lines ({len(plines)}):")
            for i, l in plines[:30]:
                prev = lines[i-1] if i>0 else ""
                log(f"    [{prev[:22]}] -> {l[:38]}")

            # Magnite trims
            for trim in ["XE","XL","XV","XV Premium","XV Premium (O)","Kuro","Visia","Acenta","Tekna"]:
                if re.search(r"\b"+re.escape(trim)+r"\b", txt):
                    log(f"    (trim: {trim})")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("nissan2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. nissan2.txt UPLOAD kar do.")
print("=" * 60)s