"""
debug_skoda6.py — Skoda configurator ke IFRAME ke andar ghus ke price API pakdo
================================================================================
Ab tak: model page pe sirf starting price. 'Build' configurator IFRAME me chalta
hai, isliye uske network calls bahar se miss ho rahe the.

Ye script:
  1. kushaq page kholta hai, 'Build/Configure/Check Price' dabata hai
  2. HAR frame (iframe) ke andar ka URL + content padhta hai
  3. Configurator ke apne network calls (kisi bhi domain) capture karta hai —
     khaas kar 'price', 'variant', 'derivative', 'trim', 'catalog', 'pricing'
     wale endpoints
  4. Iframe ke andar ki variant + ₹ prices bhi padhta hai

Browser khulega (headed) — 'Build' ke baad agar configurator dikhe to usme
1-2 variant pe click kar dena, phir terminal me ENTER.

CHALAO:
    python debug_skoda6.py
Phir skoda_debug6.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.skoda-auto.co.in"
URL = f"{BASE}/models/kushaq/kushaq"

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","doubleclick",
        "analytics","clarity","adobe","demdex","omtrdc","onetrust","hotjar","bing",
        "segment","taboola","criteo","/sync.html","sync-pn-server","laura3","cognigy",
        "webchat","sgtm.","consent","cookie"]

# ye keywords URL me ho to definitely capture (price endpoints)
PRICE_HINT = ["price","variant","derivative","trim","catalog","pricing","carline",
              "model-data","modeldata","product","configuration","spec"]

out = []
def log(s=""):
    print(s)
    out.append(str(s))


def real_prices(body):
    nums = re.findall(r'\b(\d{6,7})\b', body)
    return sorted(set(int(n) for n in nums if 100000 <= int(n) <= 9999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = ctx.new_page()

    calls = []
    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        low = u.lower()
        is_hint = any(k in low for k in PRICE_HINT)
        ct = resp.headers.get("content-type", "")
        if "json" not in ct and not is_hint:
            return
        try:
            b = resp.text()
        except Exception:
            b = ""
        # rakho agar: price-range numbers hain YA URL me price-hint hai
        if real_prices(b) or is_hint:
            calls.append((u, resp.request.method, b))
    ctx.on("response", on_response)

    opened = []
    ctx.on("page", lambda pg: opened.append(pg))

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    for label in ["Build", "Build Your Car", "Configure", "Check Price",
                  "Check price", "View Price", "Explore Price", "Get Price"]:
        try:
            el = page.locator(f"text={label}").first
            if el.count() > 0:
                el.click(timeout=3000)
                log(f"clicked '{label}'")
                page.wait_for_timeout(6000)
                break
        except Exception:
            pass

    log("\n>>> Agar configurator/price UI khula ho, usme 1-2 variant pe click")
    log(">>> karo (prices dikhne tak). Phir yahan ENTER dabao.")
    try:
        input(">>> ENTER dabao... ")
    except Exception:
        page.wait_for_timeout(15000)

    page.wait_for_timeout(2000)

    # ---- saare frames (iframes) ke andar dekho ----
    all_pages = [page] + opened
    log(f"\n=== {len(all_pages)} page(s), inke frames ===")
    for pi, pg in enumerate(all_pages):
        try:
            log(f"\npage[{pi}]: {pg.url[:110]}")
            for fr in pg.frames:
                furl = fr.url or ""
                if any(s in furl for s in SKIP) or furl in ("", "about:blank"):
                    continue
                log(f"  FRAME: {furl[:110]}")
                try:
                    ftxt = fr.locator("body").inner_text(timeout=3000)
                    fplines = [l.strip() for l in ftxt.split("\n")
                               if ("₹" in l or "Rs" in l) and re.search(r"\d", l)]
                    for l in fplines[:20]:
                        log(f"    ₹ {l[:60]}")
                    # variant naam bhi (Active/Ambition/Style/Sportline Skoda trims)
                    for trim in ["Classic","Signature","Active","Ambition","Style",
                                 "Sportline","Prestige","Laurin","Onyx","Selection"]:
                        if trim in ftxt:
                            log(f"    (trim dikha: {trim})")
                except Exception:
                    pass
        except Exception as e:
            log(f"  page err: {str(e)[:40]}")

    # ---- price-jaisi network calls ----
    log(f"\n=== network calls captured: {len(calls)} ===")
    hits = [(u, m, b, real_prices(b)) for (u, m, b) in calls]
    hits.sort(key=lambda x: -len(x[3]))
    seen = set()
    shown = 0
    for u, m, b, gp in hits:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        shown += 1
        if shown > 10:
            break
        log(f"\n  [{m}] {u[:130]}")
        log(f"  {len(gp)} price-range numbers: {gp[:20]}")
        log(f"  body: {b[:500].replace(chr(10),' ')}")

    # saare unique domains (taaki pata chale price kis domain se aa sakti hai)
    log("\n=== unique non-tracking domains dekhe ===")
    doms = sorted(set(re.match(r'https?://([^/]+)', u).group(1)
                      for u, m, b in calls if re.match(r'https?://([^/]+)', u)))
    for d in doms:
        log(f"  {d}")

    browser.close()

with open("skoda_debug6.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug6.txt UPLOAD kar do.")
print("=" * 60)