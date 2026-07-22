"""
debug_tata4.py — Tata ka asli data source (API) pakadne ke liye
================================================================
Tata ka price page JavaScript se data laata hai. Ye script dekhti hai ki
page background me kaunsi request se prices aati hain (network calls).
Agar wo JSON API mil gaya, to sab variants ek saath mil jayenge — filter
click ki zaroorat hi nahi.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"

captured = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # har network response pakdo jisme price/variant jaisa data ho
    def on_response(response):
        url = response.url
        ct = response.headers.get("content-type", "")
        if "json" in ct or url.endswith(".json"):
            try:
                body = response.text()
                # sirf wo jisme price/variant jaise shabd hon
                if any(k in body.lower() for k in ["price", "variant", "exshowroom", "ex_showroom"]):
                    captured.append((url, body[:200]))
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(6000)
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(600)
    page.wait_for_timeout(3000)

    print(f"\n=== {len(captured)} JSON response mile jisme price/variant tha ===\n")
    for i, (url, preview) in enumerate(captured[:20]):
        print(f"[{i}] {url}")
        print(f"     preview: {preview[:150]}")
        print()

    # sabse bade / relevant response ko poora save karo
    if captured:
        # sabse lamba wala shayad data hai
        page.on("response", lambda r: None)  # stop
        # dobara ek baar sab capture kar ke bada wala save karo
        with open("tata_api_urls.txt", "w", encoding="utf-8") as f:
            for url, _ in captured:
                f.write(url + "\n")
        print("Saare API URLs save hue: tata_api_urls.txt")

    browser.close()
    print("\nDONE.")
    if not captured:
        print("Koi JSON API nahi mila — matlab data HTML me hi embed hai.")
        print("Tab brochure PDF wala tarika try karenge.")