"""
debug_nexa.py — Nexa (Baleno) page ka structure dekhne ke liye
===============================================================
Ye Baleno ka price page khol ke text save karega, taaki pata chale
Nexa ka format Arena jaisa hi hai ya alag.

Chalao:  python debug_nexa.py
Nexa ka URL alag ho sakta hai — 3 URL try karta hai.
"""
from playwright.sync_api import sync_playwright

# Nexa ke possible URL patterns (jo khule wahi sahi)
URLS_TO_TRY = [
    "https://www.nexaexperience.com/price/baleno",
    "https://www.marutisuzuki.com/nexa/baleno/price",
    "https://www.nexaexperience.com/baleno/price",
    "https://www.marutisuzuki.com/nexa/cars/baleno/price",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    working_url = None
    for url in URLS_TO_TRY:
        try:
            print(f"Try kar rahe hain: {url}")
            page.goto(url, wait_until="networkidle", timeout=40000)
            page.wait_for_timeout(5000)
            txt = page.inner_text("body")
            # kya isme price (₹) aur variant (|) hai?
            if "₹" in txt and len(txt) > 500:
                print(f"  ✓ Ye URL chala! Text mila ({len(txt)} chars)")
                working_url = url
                # save karo
                with open("nexa_page_text.txt", "w", encoding="utf-8") as f:
                    f.write(txt)
                # variant + price lines dikhao
                print("\n=== '|' wali lines (variant naam) ===")
                for line in txt.split("\n"):
                    line = line.strip()
                    if "|" in line and len(line) < 60:
                        print("  ", repr(line))
                print("\n=== '₹' wali lines (price) ===")
                for line in txt.split("\n"):
                    if "₹" in line:
                        print("  ", repr(line.strip()))
                break
            else:
                print(f"  ✗ Khula par price nahi mila")
        except Exception as e:
            print(f"  ✗ Nahi khula: {str(e)[:60]}")

    browser.close()
    if working_url:
        print(f"\nDONE! Sahi URL: {working_url}")
        print("Ab 'nexa_page_text.txt' file mujhe bhej do.")
    else:
        print("\nKoi URL nahi chala. Aapko khud Nexa ki site pe jaake")
        print("Baleno ka price page URL dekhna hoga, wo mujhe batana.")