"""
debug_skoda5.py — Skoda 'Build' configurator ka asli domain/API pakdo
======================================================================
Skoda ka variant-price 'Build/Configure' configurator me hai jo ALAG domain/
iframe me chalta hai (cross.skoda-auto.com / visualizer.skoda-auto.com type).
Ye script:
  1. kushaq page pe 'Build'/'Configure' dabata hai
  2. Jo naya tab/iframe/URL khule use follow karta hai
  3. Us configurator ke SAARE network calls (har domain) capture karta hai
  4. Iframe ke andar ki bhi ₹ prices padhta hai

CHALAO:
    python debug_skoda5.py
Browser khulega — agar 'Build' dabane pe koi configurator khule to usme
ek variant select kar lena. Phir terminal me ENTER.
Phir skoda_debug5.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.skoda-auto.co.in"
URL = f"{BASE}/models/kushaq/kushaq"

SKIP = ["google","gtm","facebook","gstatic","fonts.","youtube","analytics","clarity",
        "adobe","demdex","omtrdc","onetrust","hotjar","bing","doubleclick","segment",
        "consent","matomo","piwik","optimizely","mouseflow","/sync.html","sync-pn-server"]

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

    calls = []  # (url, method, body)

    def on_response(resp):
        u = resp.url
        if any(s in u for s in SKIP):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct and "javascript" not in ct:
            # non-json bhi, agar URL me price/config/variant ho
            if not any(k in u.lower() for k in ["price","config","variant","model","catalog","trim"]):
                return
        try:
            b = resp.text()
        except Exception:
            b = ""
        calls.append((u, resp.request.method, b))

    ctx.on("response", on_response)

    # naye tab/popup ko bhi capture karo
    opened = []
    ctx.on("page", lambda pg: opened.append(pg))

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    # Build/Configure dabao
    for label in ["Build", "Build Your Car", "Configure", "Design Your", "Check Price", "Explore Price"]:
        try:
            el = page.locator(f"text={label}").first
            if el.count() > 0:
                el.click(timeout=3000)
                log(f"clicked '{label}'")
                page.wait_for_timeout(5000)
                break
        except Exception:
            pass

    log("\n>>> Agar koi configurator/price window khula ho, usme ek variant")
    log(">>> select karo (ya kuch der ruko). Phir yahan ENTER dabao.")
    try:
        input(">>> ENTER dabao... ")
    except Exception:
        page.wait_for_timeout(15000)

    page.wait_for_timeout(2000)

    # saare khule pages ki ₹ prices + URLs
    log(f"\n=== khule tabs/pages: {len(opened)+1} ===")
    all_pages = [page] + opened
    for i, pg in enumerate(all_pages):
        try:
            log(f"\n  page[{i}] URL: {pg.url[:120]}")
            # iframes
            for fr in pg.frames:
                if fr.url and fr.url != pg.url:
                    log(f"    iframe: {fr.url[:110]}")
            txt = pg.inner_text("body")
            plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
            for l in plines[:20]:
                log(f"    ₹ {l[:60]}")
        except Exception as e:
            log(f"    page read err: {str(e)[:40]}")

    # price-jaisi network calls
    log(f"\n=== network calls captured: {len(calls)} ===")
    hits = [(u, m, b, real_prices(b)) for (u, m, b) in calls]
    hits = [h for h in hits if len(h[3]) >= 2]
    hits.sort(key=lambda x: -len(x[3]))
    seen = set()
    for u, m, b, gp in hits[:8]:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        log(f"\n  [{m}] {u[:130]}")
        log(f"  {len(gp)} price-range numbers: {gp[:20]}")
        log(f"  body: {b[:500].replace(chr(10),' ')}")

    # agar kuch na mila, saare unique domains list karo (taaki pata chale kahan dekhein)
    if not hits:
        log("\n  koi price-jaisi call nahi. Saare domains jo dikhe:")
        domains = sorted(set(re.match(r'https?://([^/]+)', u).group(1)
                             for u, m, b in calls if re.match(r'https?://([^/]+)', u)))
        for d in domains:
            log(f"    {d}")

    browser.close()

with open("skoda_debug5.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. skoda_debug5.txt UPLOAD kar do.")
print("=" * 60)