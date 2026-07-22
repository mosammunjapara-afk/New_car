"""
debug_toyota5.py — 6 missing Toyota models ke sahi URL dhoondo
===============================================================
Fortuner, Hycross, Hyryder, Taisor, Camry, Legender - inke alag URL patterns
try karte hain aur dekhte hain kaunse pe variants API pakda jaata hai.
"""
from playwright.sync_api import sync_playwright

# har model ke liye kuch possible URLs
CANDIDATES = {
    "Fortuner": [
        "https://www.toyotabharat.com/showroom/fortuner/",
        "https://www.toyotabharat.com/showroom/all-new-fortuner/",
        "https://www.toyotabharat.com/showroom/the-legendary-fortuner/",
    ],
    "Innova Hycross": [
        "https://www.toyotabharat.com/showroom/innova-hycross/",
        "https://www.toyotabharat.com/showroom/hycross/",
        "https://www.toyotabharat.com/showroom/all-new-innova-hycross/",
    ],
    "Hyryder": [
        "https://www.toyotabharat.com/showroom/urban-cruiser-hyryder/",
        "https://www.toyotabharat.com/showroom/hyryder/",
        "https://www.toyotabharat.com/showroom/urban-cruiser-taisor/",
    ],
    "Taisor": [
        "https://www.toyotabharat.com/showroom/taisor/",
        "https://www.toyotabharat.com/showroom/urban-cruiser-taisor/",
    ],
    "Camry": [
        "https://www.toyotabharat.com/showroom/camry/",
        "https://www.toyotabharat.com/showroom/all-new-camry/",
    ],
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    captured = {"url": None, "count": 0}
    def on_response(resp):
        if "/variants" in resp.url and "toyotabharat" in resp.url:
            try:
                d = resp.json()
                v = d.get("variants", [])
                if v:
                    captured["url"] = resp.url
                    captured["count"] = len(v)
            except Exception: pass
    page.on("response", on_response)

    for model, urls in CANDIDATES.items():
        print(f"\n=== {model} ===")
        found = False
        for url in urls:
            captured["url"] = None; captured["count"] = 0
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=40000)
                page.wait_for_timeout(5000)
                for _ in range(8):
                    page.mouse.wheel(0, 900); page.wait_for_timeout(600)
                for _ in range(5):
                    if captured["url"]: break
                    page.wait_for_timeout(1500)
                if captured["url"]:
                    mid = captured["url"].split("/models/")[1].split("/")[0] if "/models/" in captured["url"] else "?"
                    print(f"  ✓ {url}")
                    print(f"     {captured['count']} variants, modelId={mid}")
                    found = True
                    break
                else:
                    print(f"  ✗ {url[-45:]}")
            except Exception as e:
                print(f"  ✗ {url[-45:]}: {str(e)[:30]}")
        if not found:
            print(f"  !! {model} ka koi URL nahi chala")

    browser.close()
    print("\nDONE.")