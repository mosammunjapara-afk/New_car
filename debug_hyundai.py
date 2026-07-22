"""
debug_hyundai.py — Hyundai ka price page structure + API dhoondhne ke liye
===========================================================================
Creta ka price page khol ke: (1) network me JSON API dhoondta hai (Tata jaisa),
(2) page ka text nikaalta hai (Maruti jaisa). Jo mile, wo dikhata hai.
"""
from playwright.sync_api import sync_playwright
import re, json

URLS = [
    "https://www.hyundai.com/in/en/find-a-car/creta/price",
    "https://www.hyundai.com/in/en/vehicles/creta/price",
    "https://www.hyundai.com/in/en/find-a-car/creta",
]

json_apis = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            try:
                body = resp.text()
                if any(k in body.lower() for k in ["price", "variant", "showroom"]):
                    json_apis.append((resp.url, body[:150]))
            except Exception:
                pass

    page.on("response", on_response)

    working = None
    for url in URLS:
        try:
            print(f"\n=== Try: {url} ===")
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(4000)
            for _ in range(5):
                page.mouse.wheel(0, 1200); page.wait_for_timeout(600)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            prices = re.findall(r"(₹\s*[\d,\. ]{3,}|Rs\.?\s*[\d,\. ]{3,}|[\d,\.]+\s*[Ll]akh)", txt)
            print(f"  page {len(txt)} chars, {len(prices)} price-lines")
            if len(txt) > 1000 and len(prices) > 2:
                working = url
                with open("hyundai_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                print("  ✓ Saved: hyundai_page_text.txt")
                print("  Pehli 15 price-lines:")
                for pp in prices[:15]:
                    print("    ", repr(pp.strip()))
                print("  '|' wali lines:")
                for line in txt.split("\n"):
                    line = line.strip()
                    if "|" in line and len(line) < 60:
                        print("    ", repr(line))
                break
        except Exception as e:
            print(f"  ✗ {str(e)[:60]}")

    print(f"\n=== {len(json_apis)} JSON API mile (price/variant wale) ===")
    for u, prev in json_apis[:10]:
        print(f"  {u[:80]}")
        print(f"     {prev[:100]}")

    browser.close()
    print("\nDONE. 'hyundai_page_text.txt' bhej do (agar bani).")