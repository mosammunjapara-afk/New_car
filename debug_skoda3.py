"""
debug_skoda3.py — Skoda ka variant-wise price source dhoondo
=============================================================
URLs mil gaye: /models/{model}/{model} (starting price), aur /aid/checkprice.
Ab variant-WISE prices chahiye. Ye script:
  1. /aid/checkprice khol ke saari JSON API + form dropdowns dekhega
  2. kushaq model page khol ke variant selector / API dekhega
  3. Har jagah se variant + price data pakdega

CHALAO:
    python debug_skoda3.py
Phir skoda_debug3.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

BASE = "https://www.skoda-auto.co.in"
TARGETS = [
    ("checkprice", f"{BASE}/aid/checkprice"),
    ("kushaq", f"{BASE}/models/kushaq/kushaq"),
    ("slavia", f"{BASE}/models/slavia/slavia"),
]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def looks_price(body):
    return bool(re.search(r'\d{6,7}', body))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    apis = []
    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["google","gtm","facebook","gstatic","fonts","youtube",
                                "analytics","clarity","adobe","demdex","omtrdc","onetrust",
                                "cookie","hotjar","bing","sync.html","s_aid"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            # variant/price/model wale JSON
            if looks_price(b) and any(k in b.lower() for k in
                    ["variant","price","model","trim","grade","engine","exshowroom","amount"]):
                apis.append((u, resp.request.method, b))
    page.on("response", on_response)

    for name, url in TARGETS:
        apis.clear()
        log("\n" + "=" * 70)
        log(f"TARGET: {name}  →  {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=50000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(7000)
            # scroll
            for _ in range(5):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(700)
            page.wait_for_timeout(3000)

            # clickable price/variant buttons ya tabs try karo
            for label in ["Check Price", "View Price", "Price", "Variants", "All Variants", "Explore Variants"]:
                try:
                    el = page.locator(f"text={label}").first
                    if el.count() > 0:
                        el.click(timeout=3000)
                        log(f"  clicked '{label}'")
                        page.wait_for_timeout(4000)
                except Exception:
                    pass

            # API results
            log(f"\n  --- variant/price JSON APIs ({len(apis)}) ---")
            seen = set()
            for u, m, body in apis:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                # kitni price-jaisi values?
                prices = sorted(set(re.findall(r'\d{6,7}', body)))
                log(f"  [{m}] {u[:120]}")
                log(f"       {len(prices)} price-jaise numbers: {prices[:12]}")
                log(f"       preview: {body[:300]}")
                log("")

            # page ₹ prices
            txt = page.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
            if plines:
                log(f"  Page ₹ prices ({len(plines)}):")
                for l in plines[:20]:
                    log(f"    {l[:60]}")

            # dropdowns / selects
            nsel = page.locator("select").count()
            log(f"  <select> count: {nsel}")
        except Exception as e:
            log(f"  fail: {str(e)[:70]}")

    browser.close()

with open("skoda_debug3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug3.txt UPLOAD kar do.")
print("=" * 60)