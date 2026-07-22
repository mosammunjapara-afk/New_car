"""
debug_tata8.py — Tata ke filter OPTIONS aur har fuel ka API pakadna
====================================================================
2 cheezein karta hai:
  1. getpricefilteroptions.json pakadta hai (isme fuel/edition ke codes hote hain)
  2. Diesel radio ko JavaScript se click karta hai (asli click event) aur
     dekhta hai koi naya network call hota hai kya
Isse pata chalega Diesel data kaise mangte hain.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"
captured = {"options": None, "all_urls": []}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(response):
        u = response.url
        if "getpricefilter" in u or "price" in u.lower():
            captured["all_urls"].append(u)
        if "getpricefilteroptions" in u:
            try:
                captured["options"] = response.json()
            except Exception:
                pass

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)
    for _ in range(4):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(600)
    page.wait_for_timeout(2000)

    # 1. Filter options save karo
    if captured["options"]:
        with open("tata_filter_options.json", "w", encoding="utf-8") as f:
            json.dump(captured["options"], f, indent=2)
        print("\n✓ Saved: tata_filter_options.json")
        # fuel type ke options dikhao
        opts = captured["options"].get("results", {}).get("filterOptionsList", [])
        for grp in opts:
            print(f"\n  Filter: {grp.get('filterLabel')} ({grp.get('filterType')})")
            for o in grp.get("filterOption", []):
                print(f"     - {o.get('optionValue')}  => optionId: {o.get('optionId')}")
    else:
        print("\n✗ filter options nahi mile")

    # 2. Diesel ko asli JS click do (radio input)
    print("\n--- Diesel radio ko force-click (JS) ---")
    before = len(captured["all_urls"])
    try:
        page.evaluate("""
            () => {
                const labels = [...document.querySelectorAll('*')];
                const d = labels.find(el => el.textContent.trim() === 'Diesel' && el.offsetParent);
                if (d) { d.click(); return 'clicked'; }
                return 'not found';
            }
        """)
        page.wait_for_timeout(4000)
    except Exception as e:
        print("  err:", e)
    after = len(captured["all_urls"])
    print(f"  Diesel click ke baad {after-before} naye price-call hue")

    print(f"\n=== Saare price-related URLs ({len(captured['all_urls'])}) ===")
    for u in captured["all_urls"]:
        print("  ", u)

    browser.close()
    print("\nDONE. 'tata_filter_options.json' mujhe bhej do.")