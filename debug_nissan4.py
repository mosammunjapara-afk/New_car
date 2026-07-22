"""
debug_nissan4.py — Nissan Magnite prices.html ka poora HTML save
=================================================================
HTML me price numbers hain (599900, 654675, 707025...) — asli Magnite prices.
Bas variant+price connection dhoondhna hai. Poora HTML save karo, main khud
parse karunga.

CHALAO:
    python debug_nissan4.py

Banega: nissan_magnite.html + nissan4.txt — DONO UPLOAD karo.
"""

from playwright.sync_api import sync_playwright
import re

URL = "https://www.nissan.in/vehicles/new/magnite/prices.html"

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

    log(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(6000)
    for _ in range(10):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(500)
    page.wait_for_timeout(3000)

    html = page.content()
    with open("nissan_magnite.html", "w", encoding="utf-8") as hf:
        hf.write(html)
    log(f"HTML saved: nissan_magnite.html ({len(html)} chars)")

    # quick: price numbers ke aas-paas ka text
    for pr in ["599900", "654675", "707025", "751636", "867562"]:
        i = html.find(pr)
        if i != -1:
            snippet = html[max(0,i-150):i+30]
            # tags hata ke readable
            clean = re.sub(r"<[^>]+>", " ", snippet)
            clean = re.sub(r"\s+", " ", clean).strip()
            log(f"  {pr} context: ...{clean[-90:]}")

    browser.close()

with open("nissan4.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("\n\n" + "=" * 60)
print("HO GAYA. nissan_magnite.html + nissan4.txt UPLOAD karo.")
print("=" * 60)