"""
debug_tata.py — Tata ka price page structure dekhne ke liye
============================================================
Tata Nexon ka price page khol ke (scroll karke) text nikaalta hai,
taaki pata chale Tata ka format kaisa hai.
"""
from playwright.sync_api import sync_playwright

URLS = [
    "https://cars.tatamotors.com/nexon/ice/price.html",
    "https://cars.tatamotors.com/cars/nexon/price.html",
    "https://cars.tatamotors.com/nexon/price",
    "https://www.tatamotors.com/cars/nexon/price",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    working = None
    for url in URLS:
        try:
            print(f"\n=== Try: {url} ===")
            page.goto(url, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(4000)
            for _ in range(6):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(700)
            page.wait_for_timeout(2000)
            txt = page.inner_text("body")
            import re
            prices = re.findall(r"(₹\s*[\d,\. ]{4,}|Rs\.?\s*[\d,\. ]{4,})", txt)
            print(f"  {len(prices)} price-lines mili, page {len(txt)} chars")
            if len(prices) > 3 and len(txt) > 500:
                working = url
                with open("tata_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                print(f"  ✓ Saved: tata_page_text.txt")
                print("  '|' wali lines (variant naam ho sakte hain):")
                for line in txt.split("\n"):
                    line = line.strip()
                    if "|" in line and len(line) < 60:
                        print("    ", repr(line))
                print("  Pehli 20 price-lines:")
                for pp in prices[:20]:
                    print("    ", repr(pp.strip()))
                break
        except Exception as e:
            print(f"  ✗ {str(e)[:60]}")

    browser.close()
    if working:
        print(f"\nDONE! Sahi URL: {working}")
        print("Ab 'tata_page_text.txt' mujhe bhej do.")
    else:
        print("\nKoi URL nahi chala. Chrome me Tata Nexon ka price page")
        print("kholke uska URL mujhe batao.")