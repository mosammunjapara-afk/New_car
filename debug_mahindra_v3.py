"""
debug_mahindra_v3.py — Mahindra naye models: saari network JSON capture
========================================================================
Model pages khulte hain par ₹ JS-render me. Ye script SAARI JSON/API calls
capture karta hai (koi bhi jisme price ho), aur homepage se sahi model URLs
bhi nikaalta hai.

CHALAO:
    python debug_mahindra_v3.py
Phir mahindra_v3.txt UPLOAD kar do.
"""

from playwright.sync_api import sync_playwright
import re

out = []
def log(s=""):
    print(s); out.append(str(s))


def rp(b):
    return sorted(set(int(n) for n in re.findall(r'\b(\d{6,8})\b', b) if 500000 <= int(n) <= 9999999))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page.set_default_timeout(35000)

    all_json = []
    def on_resp(resp):
        u = resp.url.lower()
        if any(s in u for s in ["google","gtm","facebook","font",".css",".png",".jpg",".svg",".woff","analytics","clarity","gstatic","adobe","doubleclick"]):
            return
        ct = resp.headers.get("content-type","")
        if "json" in ct:
            try: b = resp.text()
            except: return
            all_json.append((resp.url, b))
    page.on("response", on_resp)

    # 1. homepage se sahi model URLs
    log("Mahindra homepage se model links...")
    try:
        page.goto("https://auto.mahindra.com/", wait_until="domcontentloaded", timeout=35000)
        page.wait_for_timeout(5000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        ml = sorted(set(h for h in hrefs if any(m in h.lower() for m in ["thar","scorpio","xuv","bolero","xev","be-6","be6"])))
        log(f"  model links ({len(ml)}):")
        for h in ml[:20]:
            log(f"    {h}")
    except Exception as e:
        log(f"  fail: {str(e)[:40]}")
        ml = []

    # 2. har model page pe saari JSON capture
    test_pages = ml[:5] if ml else ["https://auto.mahindra.com/suv/thar-roxx"]
    for url in test_pages:
        all_json.clear()
        log(f"\n{'='*60}")
        log(f"PAGE: {url}")
        try:
            r = page.goto(url, wait_until="domcontentloaded", timeout=35000)
            log(f"  status: {r.status if r else '?'}")
            page.wait_for_timeout(7000)
            for _ in range(8):
                page.mouse.wheel(0,1000); page.wait_for_timeout(500)
            page.wait_for_timeout(3000)
            # price wali JSON
            price_json = [(u,b) for u,b in all_json if rp(b)]
            log(f"  total JSON: {len(all_json)}, price-wali: {len(price_json)}")
            seen=set()
            for u,b in price_json[:5]:
                base=u.split('?')[0]
                if base in seen: continue
                seen.add(base)
                log(f"    {u[:100]}")
                log(f"      prices: {rp(b)[:12]}")
                names = re.findall(r'"(?:name|variant|title|label|modelName|variantName)"\s*:\s*"([^"]{2,35})"', b)
                if names: log(f"      names: {names[:8]}")
        except Exception as e:
            log(f"  fail: {str(e)[:40]}")

    browser.close()

with open("mahindra_v3.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\nHO GAYA. mahindra_v3.txt UPLOAD kar do.")