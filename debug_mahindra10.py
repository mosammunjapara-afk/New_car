"""
debug_mahindra10.py — Thar ka modal-data.json URL pakdo (kyun 0 aaya)
======================================================================
Thar page kholte hain, network me modal-data.json dhoondte hain.
Zyada wait (loading slow ho sakti hai).
"""
from playwright.sync_api import sync_playwright

URL = "https://auto.mahindra.com/suv/thar/THRN.html"
hits = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def on_response(resp):
        u = resp.url
        if "modal-data" in u or "Visualize360" in u:
            hits.append(u)

    page.on("response", on_response)

    print(f"Kholte hain: {URL}")
    page.goto(URL, timeout=90000)
    print("  Wait kar rahe hain (60 sec, loading slow ho sakti)...")
    for i in range(20):
        page.wait_for_timeout(3000)
        page.mouse.wheel(0, 500)
        if any("modal-data" in h for h in hits):
            print(f"  ✓ modal-data mil gaya! ({i*3} sec)")
            break

    print(f"\n=== Visualize360/modal-data se related URLs ({len(hits)}) ===")
    seen = set()
    for u in hits:
        if u in seen: continue
        seen.add(u)
        print(" ", u)

    # modal-data ka exact URL
    md = [h for h in hits if "modal-data" in h]
    if md:
        print(f"\n✓✓ Thar ka modal-data URL:\n  {md[0]}")
    else:
        print("\n✗ modal-data call nahi hua. Ye model 3D config use nahi karta ya URL alag.")
        # koi Visualize360 URL mila?
        vis = [h for h in hits if "Visualize360" in h]
        if vis:
            print("  Par Visualize360 URLs mile:")
            for v in vis[:5]:
                print("   ", v)

    browser.close()
    print("\nDONE.")