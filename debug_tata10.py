"""
debug_tata10.py — Diesel click pe browser ki EXACT request capture karo
========================================================================
Jab Diesel click hota hai, browser API ko ek exact request bhejta hai.
Ye script us request ka poora detail pakadti hai:
  - method (GET/POST)
  - URL (poora, query ke saath)
  - POST body (agar hai)
  - headers
Isse pata chalega API ko sahi kaise call karna hai.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"
requests_seen = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # har REQUEST (response nahi) pakdo jo price se related ho
    def on_request(req):
        if "getpricefilter" in req.url:
            info = {
                "method": req.method,
                "url": req.url,
                "post_data": req.post_data,
                "headers": dict(req.headers),
            }
            requests_seen.append(info)

    page.on("request", on_request)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(600)
    page.wait_for_timeout(2000)

    initial = len(requests_seen)
    print(f"\nShuruaat me {initial} price-requests hui")

    # Diesel radio ko force click (JS)
    print("\n--- Diesel click karte hain ---")
    page.evaluate("""
        () => {
            const els = [...document.querySelectorAll('*')];
            const d = els.find(el => el.textContent.trim() === 'Diesel' && el.offsetParent);
            if (d) d.click();
        }
    """)
    page.wait_for_timeout(4000)

    print(f"Diesel ke baad kul {len(requests_seen)} price-requests\n")

    # sabhi requests ka detail dikhao
    print("=== SAARI PRICE-REQUESTS KA DETAIL ===")
    for i, r in enumerate(requests_seen):
        print(f"\n[{i}] {r['method']} {r['url']}")
        if r['post_data']:
            print(f"    POST BODY: {r['post_data'][:300]}")

    # poora detail file me save karo
    with open("tata_requests.json", "w", encoding="utf-8") as f:
        json.dump(requests_seen, f, indent=2)
    print("\nSaved: tata_requests.json")

    browser.close()
    print("\nDONE. 'tata_requests.json' mujhe bhej do.")