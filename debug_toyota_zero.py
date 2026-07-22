"""
debug_toyota_zero.py — Toyota Camry/Taisor/Land Cruiser 0 kyun? pata karo
==========================================================================
Ye 3 models "API nahi pakda" dete hain. Baaki Toyota theek hai.
Iska matlab in 3 ke page pe /variants API call nahi ho raha (galat URL ya
alag structure). Ye script har ek ke liye:
  1. page khula ya 404? (sahi URL check)
  2. koi /variants ya price API call hua?
  3. page pe ₹ prices dikhe?
  4. sahi showroom URL ka pata (homepage se link)

CHALAO:
    python debug_toyota_zero.py
Phir toyota_zero.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

# 3 problem models + possible URLs
TESTS = {
    "Camry": [
        "https://www.toyotabharat.com/showroom/camry/",
        "https://www.toyotabharat.com/showroom/all-new-camry/",
        "https://www.toyotabharat.com/showroom/camry/index-camry.html",
    ],
    "Taisor": [
        "https://www.toyotabharat.com/showroom/taisor/",
        "https://www.toyotabharat.com/showroom/urban-cruiser-taisor/",
        "https://www.toyotabharat.com/showroom/taisor/index-taisor.html",
    ],
    "Land Cruiser 300": [
        "https://www.toyotabharat.com/showroom/land-cruiser-300/",
        "https://www.toyotabharat.com/showroom/landcruiser-300/",
        "https://www.toyotabharat.com/showroom/land-cruiser/",
    ],
}

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

    api_calls = []
    def on_response(resp):
        u = resp.url
        if "variants" in u.lower() or ("api" in u.lower() and re.search(r'\d{6}', (lambda: _safe(resp))() or "")):
            api_calls.append((u, resp.status))
    def _safe(r):
        try: return r.text()
        except: return ""

    def on_req_variants(resp):
        u = resp.url
        if "variant" in u.lower() or "/models/" in u.lower() or "price" in u.lower():
            try:
                b = resp.text()
            except Exception:
                b = ""
            api_calls.append((u, resp.status, b[:200]))
    page.on("response", lambda r: on_req_variants(r))

    # pehle homepage se saare showroom links le lo
    log("Homepage se showroom links...")
    try:
        page.goto("https://www.toyotabharat.com/", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        hrefs = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a=>a.href)")
        show = sorted(set(h for h in hrefs if "showroom" in h.lower()
                          and any(k in h.lower() for k in ["camry","taisor","land","cruiser"])))
        log("  relevant showroom links:")
        for h in show:
            log(f"    {h}")
    except Exception as e:
        log(f"  homepage fail: {str(e)[:50]}")

    for model, urls in TESTS.items():
        log("\n" + "=" * 70)
        log(f"MODEL: {model}")
        log("=" * 70)
        for url in urls:
            api_calls.clear()
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=40000)
                st = resp.status if resp else "?"
                log(f"  [{st}] {url}")
                if st == 200:
                    page.wait_for_timeout(6000)
                    for _ in range(4):
                        page.mouse.wheel(0, 1200)
                        page.wait_for_timeout(600)
                    page.wait_for_timeout(2000)
                    # API calls
                    seen = set()
                    for item in api_calls:
                        u = item[0]
                        base = u.split("?")[0]
                        if base in seen: continue
                        seen.add(base)
                        log(f"    API: {u[:100]}")
                        if len(item) > 2 and item[2]:
                            log(f"         {item[2][:150]}")
                    # ₹ prices
                    txt = page.inner_text("body")
                    plines = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
                    if plines:
                        log(f"    ₹ prices ({len(plines)}):")
                        for l in plines[:8]:
                            log(f"      {l[:50]}")
                    else:
                        log(f"    (koi ₹ price nahi dikhi)")
                    break  # ye URL chala
            except Exception as e:
                log(f"  fail {url[:50]}: {str(e)[:40]}")

    browser.close()

with open("toyota_zero.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. toyota_zero.txt UPLOAD kar do.")
print("=" * 60)