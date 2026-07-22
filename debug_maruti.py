"""
debug_maruti.py — Maruti page pe prices kahan hain, ye pata karne ke liye
=========================================================================
Ye Swift ka price page kholta hai, JavaScript load hone deta hai, phir
page ka text ek file me save kar deta hai. Us file ko dekh ke pata chalega
ki prices kis format me hain — phir scraper theek ho jayega.

Chalao:  python debug_maruti.py
"""

from playwright.sync_api import sync_playwright

URL = "https://www.marutisuzuki.com/arena/swift/price"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print("Page khol rahe hain (thoda wait)...")
    page.goto(URL, wait_until="networkidle", timeout=60000)

    # extra wait taaki JavaScript pura load ho jaye
    page.wait_for_timeout(8000)

    # 1. Poora visible text save karo
    body_text = page.inner_text("body")
    with open("maruti_page_text.txt", "w", encoding="utf-8") as f:
        f.write(body_text)
    print(f"Text save hua: maruti_page_text.txt ({len(body_text)} chars)")

    # 2. Poora HTML bhi save karo (JS ke baad wala)
    html = page.content()
    with open("maruti_page_html.txt", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML save hua: maruti_page_html.txt ({len(html)} chars)")

    # 3. Terminal me price jaisi cheezein dikhao
    import re
    print("\n=== Text me jo bhi number/price jaisa mila ===")
    # ₹, Rs, Lakh, ya 5-7 digit numbers
    hits = re.findall(r"(₹[\s\d,\.]+|Rs[\s\d,\.]+|[\d,]+\s*[Ll]akh|\b\d{5,7}\b)", body_text)
    for h in hits[:40]:
        print("  ", repr(h.strip()))
    if not hits:
        print("  (kuch nahi mila — matlab price image me ya kisi aur jagah hai)")

    browser.close()
    print("\nDONE. Ab 'maruti_page_text.txt' file mujhe bhej do.")