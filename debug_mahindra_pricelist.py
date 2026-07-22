"""
debug_mahindra_pricelist.py — Mahindra ka /price-list page ya PDF (automatic)
==============================================================================
Model page pe prices SVG/encrypted me hain. Par Mahindra ka ek dedicated
price-list section ho sakta hai (auto.mahindra.com/price-list ya similar) jo
PDF ya table deta ho.

Ye script kuch price-list URLs + homepage se "price list" link try karta hai.

CHALAO:
    python debug_mahindra_pricelist.py
Phir mah_pl.txt UPLOAD kar do.
"""

from playwright.sync_api import sync_playwright
import re, urllib.request

out = []
def log(s=""):
    print(s); out.append(str(s))


def rp(b):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b', b) if 500000 <= int(n) <= 9999999))


# 1. seedhe PDF URLs (Mahindra apne domain pe host kar sakta)
log("=== direct PDF try ===")
PDFS = [
    "https://auto.mahindra.com/on/demandware.static/-/Sites-mahindra-content/default/price-list.pdf",
    "https://www.mahindra.com/price-list.pdf",
    "https://auto.mahindra.com/content/dam/mahindra/price-list.pdf",
]
for u in PDFS:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            d = r.read()
        log(f"  {u[:60]}: {len(d)} bytes {'PDF!' if d[:4]==b'%PDF' else ''}")
    except Exception as e:
        log(f"  {u[:55]}: {str(e)[:30]}")

# 2. site pe price-list link + dealer price pages
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(30000)

    json_hits = []
    def on_resp(resp):
        u = resp.url.lower()
        if any(s in u for s in ["google","gtm","facebook",".css",".png","font","analytics"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try: b = resp.text()
            except: return
            # price-list wali API (variant + price, SVG nahi)
            if rp(b) and ('variant' in b.lower() or 'exshowroom' in b.lower() or 'ex_showroom' in b.lower() or 'pricelist' in b.lower()):
                json_hits.append((resp.url, b))
    page.on("response", on_resp)

    URLS = [
        "https://auto.mahindra.com/price-list",
        "https://auto.mahindra.com/suv/scorpio-n/price",
        "https://auto.mahindra.com/car-price-list",
    ]
    for url in URLS:
        json_hits.clear()
        log(f"\nPAGE: {url}")
        try:
            r = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            log(f"  status: {r.status if r else '?'}")
            if r and r.status == 200:
                page.wait_for_timeout(6000)
                for _ in range(6):
                    page.mouse.wheel(0,1000); page.wait_for_timeout(500)
                # ₹ table
                txt = page.inner_text("body")
                pl = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d{4,}",l)]
                log(f"  ₹ lines: {len(pl)}")
                for l in pl[:12]: log(f"    {l[:55]}")
                if json_hits:
                    for u,b in json_hits[:2]:
                        log(f"  price-API: {u[:90]}")
                        log(f"    prices: {rp(b)[:12]}")
                # price-list link
                hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
                pls = sorted(set(h for h in hrefs if "price" in h.lower() and "list" in h.lower()))
                if pls: log(f"  price-list links: {pls[:4]}")
        except Exception as e:
            log(f"  fail: {str(e)[:40]}")

    browser.close()

with open("mah_pl.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. mah_pl.txt UPLOAD kar do.")