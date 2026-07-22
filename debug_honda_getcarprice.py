"""
debug_honda_getcarprice.py — /api/getCarPrice ka POORA request+response pakdo
=============================================================================
MIL GAYA: Honda ka asli price API = /api/getCarPrice
Har car ke /price page pe ye call hota hai. Ab iska poora detail chahiye:
  - Method (GET ya POST?)
  - Request URL + query params + POST body (carId? cityId? kya bhejta hai)
  - Response JSON (variant + price yahin honge)

Ye script honda-city/price aur honda-amaze/price kholega aur getCarPrice ka
sab kuch (request + response) honda_getcarprice.txt me save karega.

CHALAO:
    python debug_honda_getcarprice.py

Phir honda_getcarprice.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import json

BASE = "https://www.hondacarindia.com"
PAGES = ["honda-city/price", "honda-amaze/price"]

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

    captured = []  # (method, url, post_body, status, resp_body)

    def on_response(resp):
        try:
            req = resp.request
            u = resp.url
            if "getCarPrice" not in u:
                return
            post = req.post_data or ""
            try:
                body = resp.text()
            except Exception:
                body = "<<binary/empty>>"
            captured.append((req.method, u, post, resp.status, body))
        except Exception:
            pass

    page.on("response", on_response)

    # request headers bhi dekhne ke liye
    reqlog = []
    def on_request(req):
        if "getCarPrice" in req.url:
            reqlog.append((req.method, req.url, req.post_data or "",
                           dict(req.headers)))
    page.on("request", on_request)

    for pg in PAGES:
        captured.clear()
        reqlog.clear()
        url = f"{BASE}/{pg}"
        log("\n" + "=" * 70)
        log(f"PAGE: {url}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  page status: {resp.status if resp else '?'}")
            page.wait_for_timeout(8000)  # API ko trigger hone do
        except Exception as e:
            log(f"  goto fail: {str(e)[:60]}")
            continue

        # request details
        log(f"\n  --- getCarPrice REQUESTS ({len(reqlog)}) ---")
        for m, u, post, hdrs in reqlog:
            log(f"  [{m}] {u}")
            if post:
                log(f"    POST BODY: {post}")
            # relevant headers
            for hk in ["content-type", "referer", "x-requested-with", "authorization"]:
                if hk in hdrs:
                    log(f"    header {hk}: {hdrs[hk][:80]}")

        # response details
        log(f"\n  --- getCarPrice RESPONSES ({len(captured)}) ---")
        for m, u, post, st, body in captured:
            log(f"  [{m}] status={st}")
            try:
                parsed = json.loads(body)
                log("  RESPONSE JSON (full, pehle 5000 chars):")
                log(json.dumps(parsed, indent=2, ensure_ascii=False)[:5000])
            except Exception:
                log("  RESPONSE (raw, pehle 3000 chars):")
                log(body[:3000])

        # agar koi getCarPrice call hi nahi hua, to page ka poora __NEXT_DATA__ dekho
        if not captured:
            log("\n  getCarPrice trigger nahi hua — page ka embedded data check...")
            try:
                nd = page.evaluate(
                    "() => { const s=document.getElementById('__NEXT_DATA__'); return s?s.textContent:''; }")
                if nd:
                    log(f"  __NEXT_DATA__ len: {len(nd)}")
                    # price-jaisa data hai?
                    import re
                    prices = sorted(set(re.findall(r'\d{6,8}', nd)))
                    log(f"  numbers 6-8 digit: {prices[:20]}")
                    log("  __NEXT_DATA__ (pehle 3000 chars):")
                    log(nd[:3000])
            except Exception as e:
                log(f"  next_data err: {str(e)[:50]}")

    browser.close()

with open("honda_getcarprice.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. honda_getcarprice.txt UPLOAD kar do.")
print("=" * 60)