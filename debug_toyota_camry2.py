"""
debug_toyota_camry2.py — Camry/Land Cruiser: button click se variants API trigger
==================================================================================
Direct fetch CORS se block. Toh page pe hi rehke: Camry/Land Cruiser ke page pe
"Price"/"Variants"/"Explore" button click karke variants API trigger karte hain.
Jaise hi /variants fire ho, uska model-ID + data mil jayega.

CHALAO:
    python debug_toyota_camry2.py
Phir toyota_camry2.txt UPLOAD kar dena.
"""

from playwright.sync_api import sync_playwright
import re

TESTS = {
    "Camry": "https://www.toyotabharat.com/showroom/camry/",
    "Land Cruiser 300": "https://www.toyotabharat.com/showroom/land-cruiser-300/",
    "Taisor": "https://www.toyotabharat.com/showroom/urbancruiser-taisor/",
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

    variants_api = {"url": None, "body": None}
    def on_response(resp):
        u = resp.url
        if "/variants" in u and "toyotabharat" in u:
            try:
                variants_api["url"] = u
                variants_api["body"] = resp.text()
            except Exception:
                pass
    page.on("response", on_response)

    for model, url in TESTS.items():
        variants_api["url"] = None
        variants_api["body"] = None
        log("\n" + "=" * 70)
        log(f"MODEL: {model}")
        log("=" * 70)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(5000)

            # saare price/variant/explore buttons + links click
            labels = ["Price", "Prices", "View Price", "Check Price", "Variants",
                      "Explore", "Explore Price", "Grade", "Price List", "Variant",
                      "Self Explore", "Build", "Know More"]
            clicked = 0
            for lb in labels:
                try:
                    els = page.locator(f"text={lb}")
                    n = min(els.count(), 2)
                    for i in range(n):
                        try:
                            els.nth(i).scroll_into_view_if_needed(timeout=1500)
                            els.nth(i).click(timeout=1500)
                            clicked += 1
                            page.wait_for_timeout(2500)
                            if variants_api["url"]:
                                break
                        except Exception:
                            pass
                    if variants_api["url"]:
                        break
                except Exception:
                    pass

            # scroll bhi
            for _ in range(8):
                page.mouse.wheel(0, 1000)
                page.wait_for_timeout(600)
                if variants_api["url"]:
                    break
            page.wait_for_timeout(3000)

            log(f"  buttons clicked: {clicked}")
            if variants_api["url"]:
                u = variants_api["url"]
                b = variants_api["body"] or ""
                mid = re.search(r'/models/(\d+)/variants', u)
                log(f"  ✓✓ VARIANTS API: {u[:90]}")
                log(f"     model ID: {mid.group(1) if mid else '?'}")
                names = re.findall(r'"name"\s*:\s*"([^"]{2,40})"', b)
                prices = re.findall(r'"price"\s*:\s*(\d{6,8})', b)
                log(f"     {len(names)} variants: {names[:10]}")
                log(f"     prices: {prices[:10]}")
            else:
                log(f"  ✗ variants API trigger nahi hui")
                # page pe koi price dikhi?
                txt = page.inner_text("body")
                pl = [l.strip() for l in txt.split("\n") if "₹" in l and re.search(r"\d", l)]
                for l in pl[:5]:
                    log(f"     page ₹: {l[:50]}")
        except Exception as e:
            log(f"  fail: {str(e)[:50]}")

    browser.close()

with open("toyota_camry2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. toyota_camry2.txt UPLOAD kar do.")
print("=" * 60)