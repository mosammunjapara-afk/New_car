"""
debug_audi_stealth.py — Audi ko stealth mode se try (503 bypass)
=================================================================
Audi ne 503 diya tha (bot-block). Ye script stealth techniques use karta hai:
  - webdriver flag hide
  - realistic headers (Accept-Language, etc.)
  - navigator properties spoof
  - dheere human-jaisa behaviour

CHALAO:
    python debug_audi_stealth.py
Phir audi_stealth.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

BASE = "https://www.audi.in"

out = []
def log(s=""):
    print(s); out.append(str(s))


def real_prices(body):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{7,8})\b', body) if 3000000 <= int(n) <= 90000000))


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-web-security",
        ],
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        viewport={"width": 1366, "height": 768},
        extra_http_headers={
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    # webdriver hide
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-IN','en']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        window.chrome = {runtime: {}};
    """)
    page = context.new_page()
    page.set_default_timeout(40000)

    apis = []
    def on_response(resp):
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                b = resp.text()
            except Exception:
                return
            if real_prices(b) and any(k in b.lower() for k in ["variant","price","model","carline"]):
                apis.append((resp.url, b))
    page.on("response", on_response)

    log("Audi homepage (stealth)...")
    try:
        resp = page.goto(BASE, wait_until="domcontentloaded", timeout=40000)
        st = resp.status if resp else "?"
        log(f"  [{st}] {BASE} (final: {page.url})")
        if st == 200:
            page.wait_for_timeout(5000)
            hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
            kws = ["price","models","a4","a6","q3","q5","q7","q8","e-tron"]
            mlinks = sorted(set(h for h in hrefs if any(m in h.lower() for m in kws)))
            log(f"  links ({len(mlinks)}):")
            for h in mlinks[:20]:
                log(f"    {h}")

            # ek model/price page
            targets = [h for h in mlinks if any(k in h.lower() for k in ["price","models","q5","a4"])][:2]
            for url in targets:
                apis.clear()
                log(f"\n  PAGE: {url}")
                try:
                    r2 = page.goto(url, wait_until="domcontentloaded", timeout=35000)
                    log(f"    status: {r2.status if r2 else '?'}")
                    page.wait_for_timeout(5000)
                    for _ in range(6):
                        page.mouse.wheel(0, 1000); page.wait_for_timeout(500)
                    if apis:
                        for u,b in apis[:2]:
                            log(f"    API: {u[:90]}")
                            log(f"      prices: {real_prices(b)[:12]}")
                    txt = page.inner_text("body")
                    plines = [l.strip() for l in txt.split("\n") if ("₹" in l or "INR" in l) and re.search(r"\d{5,}",l)]
                    for l in plines[:12]:
                        log(f"    ₹: {l[:50]}")
                except Exception as e:
                    log(f"    fail: {str(e)[:40]}")
        else:
            log("  abhi bhi block (503/403). Alag technique chahiye.")
    except Exception as e:
        log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("audi_stealth.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. audi_stealth.txt UPLOAD kar do.")