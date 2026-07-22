"""
debug_toyota_camry.py — Camry + Land Cruiser ka asli variant API naam pakdo
============================================================================
Taisor URL fix ho gaya (urbancruiser-taisor). Ab Camry + Land Cruiser:
inke page pe /variants API fire nahi hota. Ye script inke page pe jaane wale
SAARE JSON API capture karta hai (sirf /variants nahi) — taaki asli API naam +
price data mile. Fortuner (jo CHALTA hai) bhi compare ke liye.

CHALAO:
    python debug_toyota_camry.py
Phir toyota_camry.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re, json

TESTS = {
    "Fortuner (works)": "https://www.toyotabharat.com/showroom/fortuner/index-fortuner.html",
    "Camry": "https://www.toyotabharat.com/showroom/camry/",
    "Land Cruiser 300": "https://www.toyotabharat.com/showroom/land-cruiser-300/",
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

    apis = []
    def on_response(resp):
        u = resp.url
        if any(x in u.lower() for x in ["google","gtm","facebook","gstatic","font",
                                        "youtube","analytics",".svg",".png",".jpg",".css",
                                        ".woff",".js","adobe","clarity"]):
            return
        ct = resp.headers.get("content-type", "")
        if "json" not in ct:
            return
        try:
            b = resp.text()
        except Exception:
            return
        apis.append((u, resp.status, b))
    page.on("response", on_response)

    for model, url in TESTS.items():
        apis.clear()
        log("\n" + "=" * 70)
        log(f"MODEL: {model}")
        log("=" * 70)
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=45000)
            log(f"  status: {resp.status if resp else '?'}")
            page.wait_for_timeout(6000)
            for _ in range(10):
                page.mouse.wheel(0, 900)
                page.wait_for_timeout(600)
            page.wait_for_timeout(4000)

            log(f"  JSON APIs captured: {len(apis)}")
            seen = set()
            for u, st, b in apis:
                base = u.split("?")[0]
                if base in seen:
                    continue
                seen.add(base)
                prices = sorted(set(int(x) for x in re.findall(r'\b(\d{6,8})\b', b) if 200000 <= int(x) <= 99999999))
                has_variant = '"variant' in b.lower() or '"name"' in b.lower()
                flag = ""
                if prices and has_variant:
                    flag = "  <== VARIANT+PRICE?"
                log(f"    [{st}] {u[:100]}{flag}")
                if prices and has_variant:
                    names = re.findall(r'"name"\s*:\s*"([^"]{2,40})"', b)
                    log(f"         prices: {prices[:12]}")
                    log(f"         names: {names[:12]}")
                    log(f"         sample: {b[:300].replace(chr(10),' ')}")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("toyota_camry.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. toyota_camry.txt UPLOAD kar do.")
print("=" * 60)