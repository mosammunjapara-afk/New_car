"""
debug_skoda4.py — Skoda variant prices: saare JSON dump karo (tracking chhod ke)
=================================================================================
Pichhle numbers timestamps the (tracking service). Asli prices Skoda ke
"visualizer"/pricing system me hain. Ye script kushaq page + checkprice page pe
HAR JSON response capture karega (tracking domains chhod ke) aur jisme sabse
zyada price-jaise numbers (5-7 digit, 100000-9999999 range) hain use dikhayega.

CHALAO:
    python debug_skoda4.py
Phir skoda_debug4.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.skoda-auto.co.in"
TARGETS = [
    ("kushaq", f"{BASE}/models/kushaq/kushaq"),
    ("checkprice", f"{BASE}/aid/checkprice"),
]

# Tracking / non-price domains — inhe poori tarah skip
SKIP = ["google","gtm","facebook","gstatic","fonts","youtube","analytics","clarity",
        "adobe","demdex","omtrdc","onetrust","cookie","hotjar","bing","sync.html",
        "sync-pn-server","s_aid","doubleclick","segment","cross.skoda","cdn-cgi",
        "consent","tags","matomo","piwik","optimizely","mouseflow"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    """100000-9999999 range ke numbers (asli car price range)."""
    nums = re.findall(r'\b(\d{6,7})\b', body)
    good = sorted(set(int(n) for n in nums if 100000 <= int(n) <= 9999999))
    return good


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # HEADED — aap dekh paoge
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    all_json = []  # (url, method, body)
    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            b = resp.text()
        except Exception:
            return
        all_json.append((u, resp.request.method, b))
    page.on("response", on_response)

    for name, url in TARGETS:
        all_json.clear()
        log("\n" + "=" * 70)
        log(f"TARGET: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)

            # "Check Price" / price buttons click karke variant flow trigger karo
            for label in ["Check Price", "Check price", "View Price", "Explore Price",
                          "Build", "Configure", "Variants", "All Variants", "Price"]:
                try:
                    el = page.locator(f"text={label}").first
                    if el.count() > 0:
                        el.click(timeout=3000)
                        log(f"  clicked '{label}'")
                        page.wait_for_timeout(4000)
                except Exception:
                    pass

            page.wait_for_timeout(3000)
            for _ in range(4):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(600)
            page.wait_for_timeout(2000)

            # saare JSON me se jinme asli price-range numbers hain
            log(f"\n  captured {len(all_json)} JSON responses (tracking chhod ke)")
            hits = []
            for u, m, b in all_json:
                gp = real_prices(b)
                if len(gp) >= 3:  # 3+ price-jaise numbers = sambhavtah variant prices
                    hits.append((u, m, b, gp))
            hits.sort(key=lambda x: -len(x[3]))

            log(f"  price-jaisi API hits: {len(hits)}")
            seen = set()
            for u, m, b, gp in hits[:6]:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                log("\n  " + "-" * 60)
                log(f"  [{m}] {u[:130]}")
                log(f"  {len(gp)} price-range numbers: {gp[:20]}")
                log(f"  BODY (pehle 800 chars):")
                log("  " + b[:800].replace("\n", " "))

            # page pe ₹ prices
            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
            if plines:
                log(f"\n  Page ₹ prices ({len(plines)}):")
                for l in plines[:20]:
                    log(f"    {l[:70]}")

            log(f"\n  final URL: {page.url}")
        except Exception as e:
            log(f"  fail: {str(e)[:70]}")

    browser.close()

with open("skoda_debug4.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug4.txt UPLOAD kar do.")
print("=" * 60)