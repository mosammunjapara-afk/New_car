"""
debug_tata2.py — Tata Nexon ka poora page text nikaalne ke liye
================================================================
Pehla URL (nexon/ice/price.html) khula tha aur kuch prices diye the.
Ye script us page ka POORA text save karti hai (khoob scroll karke),
taaki dekh saken variants aur prices kaise hain.
"""
from playwright.sync_api import sync_playwright

URL = "https://cars.tatamotors.com/nexon/ice/price.html"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)

    # khoob scroll karo (upar-neeche) taaki saara content load ho
    for _ in range(10):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(600)
    page.wait_for_timeout(2000)

    txt = page.inner_text("body")
    with open("tata_page_text.txt", "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"Saved: tata_page_text.txt ({len(txt)} chars)")

    import re
    # saari price jaisi lines
    print("\n=== Price-jaisi lines (₹ / Rs / Lakh) ===")
    hits = re.findall(r"(₹\s*[\d,\. ]{3,}|Rs\.?\s*[\d,\. ]{3,}|[\d,\.]+\s*[Ll]akh)", txt)
    for h in hits[:30]:
        print("  ", repr(h.strip()))
    if not hits:
        print("  (koi price nahi mili — prices click/tab ke peeche hongi)")

    # variant jaisi lines (chhoti lines jo capital se shuru)
    print("\n=== Chhoti lines (variant naam ho sakte hain) ===")
    for line in txt.split("\n"):
        line = line.strip()
        if 2 < len(line) < 30 and line[0].isupper() and not line.startswith(("Explore","Download","Book","Build")):
            print("  ", repr(line))

    browser.close()
    print("\nDONE. 'tata_page_text.txt' mujhe bhej do.")