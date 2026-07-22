"""
debug_tata_why0.py — Tata ab 0 cars kyun de raha hai, pata karo
=================================================================
Tata scraper page khol ke browser ka POST body (getpricefilteredresult) capture
karta hai. Ab wo capture nahi ho raha (sab models 0). Ye script Nexon page pe
jaake dekhega:
  1. Page khula ya nahi (status)
  2. getpricefilteredresult POST hua ya nahi
  3. Agar hua to uski body + response
  4. Page pe koi price dikhi ya nahi
  5. Koi naya/alag price API to nahi aa raha

Sab honda_... nahi, "tata_why0.txt" me save hoga.

CHALAO:
    python debug_tata_why0.py
Phir tata_why0.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import json, re

BASE = "https://cars.tatamotors.com"
SLUG = "nexon"
URL = f"{BASE}/{SLUG}/ice/price.html"

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

    posts = []       # (url, method, body)
    json_apis = []   # (url, status, preview)

    def on_request(req):
        if "getpricefilteredresult" in req.url:
            posts.append((req.url, req.method, req.post_data or ""))

    def on_response(resp):
        u = resp.url
        if any(x in u for x in ["google","gtm","facebook","gstatic","fonts",
                                "youtube","analytics","clarity","adobe","demdex",
                                "omtrdc","sha256","chat"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            # price-jaisa data?
            if re.search(r'\d{6,7}', b) or "price" in u.lower() or "variant" in b.lower():
                json_apis.append((u, resp.status, b[:300]))

    page.on("request", on_request)
    page.on("response", on_response)

    log(f"Kholte hain: {URL}")
    try:
        resp = page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        log(f"page status: {resp.status if resp else '?'}")
    except Exception as e:
        log(f"goto FAIL: {str(e)[:80]}")

    page.wait_for_timeout(5000)
    # scroll to trigger lazy price load
    for _ in range(5):
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(700)
    page.wait_for_timeout(4000)

    # 1. POST capture hua?
    log(f"\n=== getpricefilteredresult POSTs: {len(posts)} ===")
    for u, m, body in posts:
        log(f"  [{m}] {u}")
        log(f"  body (pehle 500): {body[:500]}")

    # 2. saare price-jaise JSON API
    log(f"\n=== price-jaise JSON APIs: {len(json_apis)} ===")
    seen = set()
    for u, st, prev in json_apis:
        base = u.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        log(f"  [{st}] {u[:120]}")
        log(f"       {prev[:200]}")

    # 3. page pe price dikhi?
    try:
        txt = page.inner_text("body")
        plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
        log(f"\n=== Page pe ₹ prices: {len(plines)} ===")
        for l in plines[:20]:
            log(f"  {l[:60]}")
    except Exception as e:
        log(f"body read err: {str(e)[:50]}")

    # 4. current URL (redirect to kahin nahi hua?)
    log(f"\nfinal URL: {page.url}")

    # 5. price.html ke alag path check
    for alt in ["/nexon/price.html", "/nexon.html", "/nexon/ice.html"]:
        try:
            r = page.evaluate("""async (u) => {
                try { const x = await fetch(u); return x.status; } catch(e){ return String(e); }
            }""", BASE + alt)
            log(f"  alt path {alt} -> {r}")
        except Exception:
            pass

    browser.close()

with open("tata_why0.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. tata_why0.txt UPLOAD kar do.")
print("=" * 60)