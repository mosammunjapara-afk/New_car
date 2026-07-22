"""
debug_tata9.py — API ko fuel code ke saath call karke Diesel/CNG data lena
===========================================================================
Fuel codes mil gaye:
  Petrol = 5-29KIJOIL, Diesel = 1-ID-1738, CNG = 1-ID-268

Ab page ke andar se (session ke saath) fetch karte hain — har fuel ke liye
API ko us fuel ke parameter ke saath call karte hain. Ye JavaScript fetch
page ke context me chalega, isliye session/token apne aap lag jayega.
"""
from playwright.sync_api import sync_playwright
import json

URL = "https://cars.tatamotors.com/nexon/ice/price.html"

FUELS = {
    "Petrol": "5-29KIJOIL",
    "Diesel": "1-ID-1738",
    "CNG": "1-ID-268",
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    print(f"Kholte hain: {URL}")
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4000)

    # base API path (bina query) — page ke andar se fetch karenge alag-alag params ke saath
    base = "https://cars.tatamotors.com/nexon/ice/price.getpricefilteredresult.json"

    # kuch alag query patterns try karte hain (Tata aise hi kuch use karta hai)
    for fuel_name, code in FUELS.items():
        print(f"\n=== {fuel_name} (code {code}) ===")
        # 3 alag URL format try karo
        candidates = [
            f"{base}?fuel_type={code}",
            f"{base}?fuel_type={code}&edition=standard",
            f"{base}?filterType=fuel_type&optionId={code}",
        ]
        for cand in candidates:
            try:
                # page ke andar fetch (session ke saath)
                result = page.evaluate("""
                    async (url) => {
                        try {
                            const r = await fetch(url, {headers: {'Accept':'application/json'}});
                            if (!r.ok) return {err: r.status};
                            const j = await r.json();
                            return j;
                        } catch(e) { return {err: String(e)}; }
                    }
                """, cand)
                if isinstance(result, dict) and result.get("results"):
                    variants = result["results"].get("variantPriceFeatures", [])
                    print(f"  ✓ {cand[-60:]}")
                    print(f"     {len(variants)} variants:")
                    for v in variants[:20]:
                        label = v.get("variantLabel","?")
                        price = v.get("priceDetails",{}).get("originalPrice","?")
                        print(f"       {label:35s} {price}")
                    break
                else:
                    print(f"  ✗ {cand[-50:]} -> {str(result)[:60]}")
            except Exception as e:
                print(f"  ✗ error: {str(e)[:50]}")

    browser.close()
    print("\nDONE.")