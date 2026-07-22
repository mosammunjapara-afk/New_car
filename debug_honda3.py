"""
debug_honda3.py — Honda Next.js JSON se variants + prices (fixed)
==================================================================
"""
from playwright.sync_api import sync_playwright
import json, re

CARS = ["honda-city", "honda-amaze", "honda-amaze-2g", "honda-elevate", "honda-zrv"]
found = {"build_id": None}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def grab_build(resp):
        m = re.search(r"/_next/data/([^/]+)/", resp.url)
        if m and not found["build_id"]:
            found["build_id"] = m.group(1)

    page.on("response", grab_build)

    print("City page khol ke BUILD_ID nikaalte hain...")
    page.goto("https://www.hondacarindia.com/honda-city", wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    for _ in range(5):
        page.mouse.wheel(0, 1000); page.wait_for_timeout(500)

    build_id = found["build_id"]
    print(f"  BUILD_ID: {build_id}")

    if not build_id:
        html = page.content()
        m = re.search(r'"buildId":"([^"]+)"', html)
        if m:
            build_id = m.group(1)
            print(f"  HTML se BUILD_ID: {build_id}")

    if build_id:
        for car in CARS:
            for suffix in ["tech-specs", "price", "variants", ""]:
                url = f"https://www.hondacarindia.com/_next/data/{build_id}/{car}"
                url += f"/{suffix}.json" if suffix else ".json"
                try:
                    page.goto(url, timeout=25000)
                    b = page.inner_text("body").strip()
                    if b.startswith("{") and "price" in b.lower():
                        data = json.loads(b)
                        raw = json.dumps(data)
                        prices = re.findall(r'"PN_[A-Za-z]*[Pp]rice[A-Za-z]*"\s*:\s*"?([\d,]+)', raw)
                        variants = re.findall(r'"PN_(?:Variant|Grade|Model|Trim)[A-Za-z]*"\s*:\s*"([^"]+)"', raw)
                        if prices:
                            print(f"\n  ✓✓ {car}/{suffix or 'main'}.json — {len(prices)} prices!")
                            print(f"     sample prices: {prices[:8]}")
                            print(f"     sample variants: {variants[:8]}")
                            fname = f"honda_{car}.json"
                            with open(fname, "w", encoding="utf-8") as f:
                                f.write(b)
                            print(f"     Saved: {fname}")
                            break
                except Exception:
                    pass
    else:
        print("  BUILD_ID nahi mila.")

    browser.close()
    print("\nDONE. honda_honda-city.json bhej do (agar bani).")